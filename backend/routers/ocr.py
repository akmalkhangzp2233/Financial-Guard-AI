"""
Phase: OCR Bill Scanner.

Flow:
user uploads a photo of a receipt
-> Tesseract extracts raw text
-> regex parsing pulls out total amount / merchant name / date
-> category is guessed using keyword matching
-> parsed draft is returned to the frontend
-> user reviews/edits it
-> user confirms
-> normal POST /transactions/ saves it.

OCR does NOT automatically create a transaction.
The user must confirm the extracted information first.

The OCR scan is also logged in receipt_scans for the audit trail.
"""

import io
import os
import re
from datetime import date
from typing import Optional

import pytesseract
from PIL import Image, ImageOps, ImageFilter

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from auth import get_current_user


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================
#
# Windows:
#   C:\Program Files\Tesseract-OCR\tesseract.exe
#
# Render / Docker / Linux:
#   /usr/bin/tesseract
#
# This automatically selects the correct executable depending
# on the operating system.
# ============================================================

if os.name == "nt":
    windows_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if os.path.exists(windows_tesseract):
        pytesseract.pytesseract.tesseract_cmd = windows_tesseract
else:
    linux_tesseract = "/usr/bin/tesseract"

    if os.path.exists(linux_tesseract):
        pytesseract.pytesseract.tesseract_cmd = linux_tesseract


router = APIRouter(prefix="/ocr", tags=["ocr"])


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FILE_SIZE_MB = 8

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}


# ============================================================
# CATEGORY KEYWORDS
# ============================================================

CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "restaurant",
        "cafe",
        "coffee",
        "pizza",
        "food",
        "kitchen",
        "diner",
        "bakery",
        "bar",
        "grill",
        "eatery",
        "swiggy",
        "zomato",
        "mcdonald",
        "starbucks",
        "dominos",
        "kfc",
        "burger",
    ],

    "Transport": [
        "uber",
        "ola",
        "taxi",
        "cab",
        "fuel",
        "petrol",
        "diesel",
        "metro",
        "parking",
        "fastag",
    ],

    "Shopping": [
        "mart",
        "store",
        "shop",
        "retail",
        "amazon",
        "flipkart",
        "mall",
        "supermarket",
        "grocery",
    ],

    "Utilities": [
        "electricity",
        "water bill",
        "gas bill",
        "broadband",
        "wifi",
        "recharge",
        "utility",
    ],

    "Health": [
        "pharmacy",
        "hospital",
        "clinic",
        "medical",
        "chemist",
        "diagnostic",
        "medicine",
    ],

    "Entertainment": [
        "cinema",
        "movie",
        "theatre",
        "netflix",
        "spotify",
        "multiplex",
        "pvr",
        "inox",
    ],

    "Education": [
        "school",
        "college",
        "university",
        "tuition",
        "course",
        "books",
        "academy",
    ],
}


# ============================================================
# REGEX PATTERNS
# ============================================================

# Examples:
# 1234.56
# 1,234.56
# Rs. 1234
# $12.34
# INR 500

_AMOUNT_RE = re.compile(
    r"(?:rs\.?|inr|\$|usd)?\s*"
    r"([0-9]{1,3}(?:[,.][0-9]{2,3})*(?:\.[0-9]{2})?)",
    re.IGNORECASE,
)


_TOTAL_LINE_RE = re.compile(
    r"(grand\s*total|total\s*amount|total|amount\s*due|"
    r"balance\s*due|net\s*payable)",
    re.IGNORECASE,
)


_DATE_PATTERNS = [
    (
        re.compile(
            r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b"
        ),
        "dmy",
    ),
    (
        re.compile(
            r"\b(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})\b"
        ),
        "ymd",
    ),
]


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def _preprocess(image_bytes: bytes) -> Image.Image:
    """
    Improve receipt image quality before sending it to Tesseract.

    Steps:
    1. Open image
    2. Convert to grayscale
    3. Increase contrast
    4. Sharpen
    5. Upscale small images
    """

    img = Image.open(io.BytesIO(image_bytes))

    img = img.convert("L")

    img = ImageOps.autocontrast(img)

    img = img.filter(ImageFilter.SHARPEN)

    if img.width < 1000:
        scale = 1000 / img.width

        img = img.resize(
            (
                int(img.width * scale),
                int(img.height * scale),
            )
        )

    return img


# ============================================================
# AMOUNT EXTRACTION
# ============================================================

def _extract_amount(text: str) -> Optional[float]:
    """
    Prefer amounts found on TOTAL / AMOUNT DUE lines.

    If no total line is detected, use the largest plausible
    currency value found on the receipt.
    """

    lines = text.splitlines()

    candidates_on_total_lines = []
    all_candidates = []

    for line in lines:

        matches = _AMOUNT_RE.findall(line)

        for match in matches:

            cleaned = match.replace(",", "")

            try:
                value = float(cleaned)

            except ValueError:
                continue

            if value <= 0 or value > 10_000_000:
                continue

            all_candidates.append(value)

            if _TOTAL_LINE_RE.search(line):
                candidates_on_total_lines.append(value)

    if candidates_on_total_lines:
        return max(candidates_on_total_lines)

    if all_candidates:
        return max(all_candidates)

    return None


# ============================================================
# DATE EXTRACTION
# ============================================================

def _extract_date(text: str) -> Optional[date]:

    today = date.today()

    for pattern, order in _DATE_PATTERNS:

        match = pattern.search(text)

        if not match:
            continue

        try:

            if order == "dmy":

                d, mo, y = match.groups()

            else:

                y, mo, d = match.groups()

            y = int(y)

            if y < 100:
                y += 2000

            candidate = date(
                y,
                int(mo),
                int(d),
            )

            if candidate.year >= 2000 and candidate <= today:
                return candidate

        except ValueError:
            continue

    return None


# ============================================================
# MERCHANT EXTRACTION
# ============================================================

def _extract_merchant(text: str) -> Optional[str]:
    """
    Try to identify the merchant name from the first few
    non-empty OCR lines.
    """

    for line in text.splitlines()[:8]:

        cleaned = line.strip()

        if (
            2 <= len(cleaned) <= 40
            and sum(c.isalpha() for c in cleaned)
            >= max(2, len(cleaned) // 2)
        ):
            return cleaned

    return None


# ============================================================
# CATEGORY SUGGESTION
# ============================================================

def _suggest_category(
    db: Session,
    merchant: Optional[str],
    raw_text: str,
):
    """
    Guess a category using merchant name and OCR text.

    The category is then looked up in the actual database,
    so the ID comes from the current category table.
    """

    haystack = f"{merchant or ''} {raw_text}".lower()

    for category_name, keywords in CATEGORY_KEYWORDS.items():

        if any(keyword in haystack for keyword in keywords):

            category = (
                db.query(models.Category)
                .filter(models.Category.name == category_name)
                .first()
            )

            if category:
                return category

    # Fallback:
    # Prefer Shopping if it exists.
    # Otherwise use the first non-income category.

    fallback = (
        db.query(models.Category)
        .filter(models.Category.name == "Shopping")
        .first()
    )

    if fallback:
        return fallback

    return (
        db.query(models.Category)
        .filter(models.Category.is_income == False)
        .first()
    )


# ============================================================
# SCAN RECEIPT
# ============================================================

@router.post(
    "/scan-receipt",
    response_model=schemas.ReceiptScanOut,
)
async def scan_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):

    # --------------------------------------------------------
    # Validate file type
    # --------------------------------------------------------

    if file.content_type not in ALLOWED_CONTENT_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Upload a JPEG, PNG, or WebP photo "
                "of the receipt."
            ),
        )

    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    raw_bytes = await file.read()

    # --------------------------------------------------------
    # Validate file size
    # --------------------------------------------------------

    if len(raw_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:

        raise HTTPException(
            status_code=400,
            detail=(
                f"File too large "
                f"(max {MAX_FILE_SIZE_MB}MB)."
            ),
        )

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    try:

        image = _preprocess(raw_bytes)

        raw_text = pytesseract.image_to_string(image)

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail=f"Could not read this image: {exc}",
        )

    # --------------------------------------------------------
    # Extract information
    # --------------------------------------------------------

    amount = _extract_amount(raw_text)

    merchant = _extract_merchant(raw_text)

    parsed_date = (
        _extract_date(raw_text)
        or date.today()
    )

    category = _suggest_category(
        db,
        merchant,
        raw_text,
    )

    # --------------------------------------------------------
    # Confidence score
    # --------------------------------------------------------

    found = sum(
        value is not None
        for value in [amount, merchant]
    )

    if raw_text.strip():

        confidence = round(
            (found / 2)
            * (0.9 if amount and merchant else 0.5),
            2,
        )

    else:

        confidence = 0.0

    # --------------------------------------------------------
    # Save scan to database
    # --------------------------------------------------------

    scan = models.ReceiptScan(
        user_id=current_user.id,
        original_filename=file.filename,
        raw_text=raw_text[:4000],
        parsed_amount=amount,
        parsed_merchant=merchant,
        parsed_date=parsed_date,
        suggested_category_id=(
            category.id if category else None
        ),
        confidence=confidence,
    )

    db.add(scan)

    db.commit()

    db.refresh(scan)

    # --------------------------------------------------------
    # Return parsed receipt to frontend
    # --------------------------------------------------------

    return schemas.ReceiptScanOut(
        scan_id=scan.id,
        raw_text=raw_text,
        parsed_amount=amount,
        parsed_merchant=merchant,
        parsed_date=parsed_date,
        suggested_category_id=(
            category.id if category else None
        ),
        suggested_category_name=(
            category.name if category else None
        ),
        confidence=confidence,
    )


# ============================================================
# LINK SCAN TO TRANSACTION
# ============================================================

@router.post(
    "/scans/{scan_id}/link/{transaction_id}"
)
def link_scan_to_transaction(
    scan_id: int,
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Called after the frontend saves the confirmed
    transaction.

    This connects the OCR scan to the resulting transaction.
    """

    scan = (
        db.query(models.ReceiptScan)
        .filter(
            models.ReceiptScan.id == scan_id,
            models.ReceiptScan.user_id == current_user.id,
        )
        .first()
    )

    if not scan:

        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    txn = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == transaction_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )

    if not txn:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    scan.resulting_transaction_id = txn.id

    db.commit()

    return {
        "ok": True
    }


# ============================================================
# OCR SCAN HISTORY
# ============================================================

@router.get("/scans/history")
def scan_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):

    scans = (
        db.query(models.ReceiptScan)
        .filter(
            models.ReceiptScan.user_id
            == current_user.id
        )
        .order_by(
            models.ReceiptScan.created_at.desc()
        )
        .limit(25)
        .all()
    )

    return [
        {
            "id": scan.id,
            "original_filename": scan.original_filename,
            "parsed_amount": scan.parsed_amount,
            "parsed_merchant": scan.parsed_merchant,
            "confidence": scan.confidence,
            "resulting_transaction_id": (
                scan.resulting_transaction_id
            ),
            "created_at": scan.created_at,
        }
        for scan in scans
    ]

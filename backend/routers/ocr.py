"""
Phase: OCR Bill Scanner.

Flow:
User uploads a receipt -> Tesseract OCR extracts text ->
amount / merchant / date are parsed -> category is suggested ->
frontend shows the parsed draft -> user reviews and confirms ->
normal transaction endpoint saves it.

The OCR result is NOT automatically saved as a transaction.
"""

import io
import os
import re
import shutil
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


router = APIRouter(prefix="/ocr", tags=["ocr"])


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

def _configure_tesseract():
    """
    Works both locally on Windows and inside Render's Linux Docker container.

    Windows:
        C:\\Program Files\\Tesseract-OCR\\tesseract.exe

    Linux / Render:
        /usr/bin/tesseract
    """

    # First try PATH.
    tesseract_path = shutil.which("tesseract")

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        return

    # Windows fallback.
    windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if os.path.exists(windows_path):
        pytesseract.pytesseract.tesseract_cmd = windows_path
        return

    # If neither exists, OCR will produce a clear error later.
    pytesseract.pytesseract.tesseract_cmd = "tesseract"


_configure_tesseract()


# ============================================================
# CONFIG
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
# REGEX
# ============================================================

_AMOUNT_RE = re.compile(
    r"(?:rs\.?|inr|\$|usd)?\s*"
    r"([0-9]{1,3}(?:[,.][0-9]{2,3})*(?:\.[0-9]{2})?)",
    re.IGNORECASE,
)

_TOTAL_LINE_RE = re.compile(
    r"(grand\s*total|total\s*amount|total|amount\s*due|"
    r"balance\s*due|net\s*payable|amount\s*paid)",
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
    Basic preprocessing to improve Tesseract OCR accuracy.

    Steps:
    - Open image
    - Convert to grayscale
    - Increase contrast
    - Sharpen
    - Upscale small images
    """

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:
        raise ValueError(f"Invalid image file: {exc}")

    img = img.convert("L")

    img = ImageOps.autocontrast(img)

    img = img.filter(ImageFilter.SHARPEN)

    if img.width < 1200:
        scale = 1200 / img.width

        new_width = int(img.width * scale)
        new_height = int(img.height * scale)

        img = img.resize((new_width, new_height))

    return img


# ============================================================
# AMOUNT EXTRACTION
# ============================================================

def _extract_amount(text: str) -> Optional[float]:
    """
    Prefer amounts appearing on TOTAL / AMOUNT DUE lines.

    If no total line exists, use the largest plausible amount
    found in the receipt.
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

            if value <= 0:
                continue

            if value > 10_000_000:
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
    """
    Extract receipt date.

    Supports:
        DD/MM/YYYY
        DD-MM-YYYY
        DD.MM.YYYY
        YYYY-MM-DD
    """

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

            # Do not accept dates before 2000
            # or dates in the future.
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
    Approximate merchant name from the first few meaningful lines.
    """

    lines = text.splitlines()

    checked_lines = 0

    for line in lines:

        cleaned = line.strip()

        if not cleaned:
            continue

        checked_lines += 1

        if checked_lines > 10:
            break

        # Ignore lines that are obviously numbers.
        if not any(c.isalpha() for c in cleaned):
            continue

        # Avoid extremely long OCR paragraphs.
        if len(cleaned) > 60:
            continue

        alpha_count = sum(
            c.isalpha()
            for c in cleaned
        )

        if alpha_count >= max(2, len(cleaned) // 2):

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
    Suggest a category using merchant + OCR text.

    Category names are looked up from the database, so the
    actual category IDs remain database-controlled.
    """

    haystack = (
        f"{merchant or ''} {raw_text}"
    ).lower()

    for category_name, keywords in CATEGORY_KEYWORDS.items():

        for keyword in keywords:

            if keyword.lower() in haystack:

                category = (
                    db.query(models.Category)
                    .filter(
                        models.Category.name == category_name
                    )
                    .first()
                )

                if category:
                    return category

    # Default fallback.
    shopping = (
        db.query(models.Category)
        .filter(
            models.Category.name == "Shopping"
        )
        .first()
    )

    if shopping:
        return shopping

    # Last fallback: first non-income category.
    fallback = (
        db.query(models.Category)
        .filter(
            models.Category.is_income.is_(False)
        )
        .first()
    )

    return fallback


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
    # Read file
    # --------------------------------------------------------

    raw_bytes = await file.read()

    # --------------------------------------------------------
    # Validate file size
    # --------------------------------------------------------

    if len(raw_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:

        raise HTTPException(
            status_code=400,
            detail=(
                f"File too large. Maximum size is "
                f"{MAX_FILE_SIZE_MB}MB."
            ),
        )

    if not raw_bytes:

        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty.",
        )

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    try:

        image = _preprocess(raw_bytes)

        raw_text = pytesseract.image_to_string(
            image,
            config="--psm 6",
        )

    except Exception as exc:

        error_text = str(exc)

        # Give a cleaner deployment-specific error.
        if (
            "tesseract" in error_text.lower()
            or "not found" in error_text.lower()
        ):

            raise HTTPException(
                status_code=422,
                detail=(
                    "Tesseract OCR is not available on "
                    "the backend server."
                ),
            )

        raise HTTPException(
            status_code=422,
            detail=(
                "Could not read this image. "
                "Please try a clearer receipt photo."
            ),
        )

    # --------------------------------------------------------
    # Check OCR result
    # --------------------------------------------------------

    if not raw_text.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Could not read that receipt. "
                "Try a clearer photo."
            ),
        )

    # --------------------------------------------------------
    # Parse receipt
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
    # Confidence
    # --------------------------------------------------------

    found = sum(
        value is not None
        for value in [amount, merchant]
    )

    if raw_text.strip():

        confidence = round(
            (found / 2)
            * (
                0.9
                if amount is not None
                and merchant is not None
                else 0.5
            ),
            2,
        )

    else:

        confidence = 0.0

    # --------------------------------------------------------
    # Save OCR audit record
    # --------------------------------------------------------

    scan = models.ReceiptScan(
        user_id=current_user.id,
        original_filename=file.filename,
        raw_text=raw_text[:4000],
        parsed_amount=amount,
        parsed_merchant=merchant,
        parsed_date=parsed_date,
        suggested_category_id=(
            category.id
            if category
            else None
        ),
        confidence=confidence,
    )

    db.add(scan)

    db.commit()

    db.refresh(scan)

    # --------------------------------------------------------
    # Return parsed draft
    # --------------------------------------------------------

    return schemas.ReceiptScanOut(
        scan_id=scan.id,
        raw_text=raw_text,
        parsed_amount=amount,
        parsed_merchant=merchant,
        parsed_date=parsed_date,
        suggested_category_id=(
            category.id
            if category
            else None
        ),
        suggested_category_name=(
            category.name
            if category
            else None
        ),
        confidence=confidence,
    )


# ============================================================
# LINK OCR SCAN TO TRANSACTION
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
            detail="Scan not found.",
        )

    transaction = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == transaction_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )

    if not transaction:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    scan.resulting_transaction_id = transaction.id

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

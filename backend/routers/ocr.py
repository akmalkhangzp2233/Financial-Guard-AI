"""
Phase: OCR Bill Scanner.

Flow: user uploads a photo of a receipt -> Tesseract extracts raw text ->
regex parsing pulls out total amount / merchant name / date -> we guess a
category by keyword-matching the merchant name against known categories ->
the parsed draft is returned to the frontend for the user to review and edit
-> user confirms -> a normal POST /transactions/ call saves it (which then
also runs through the existing fraud model, same as manual entries).

We deliberately DON'T auto-save straight into transactions: OCR on a phone
photo of a crumpled receipt is never 100% reliable, and silently creating a
wrong transaction is worse than asking for one tap of confirmation. This
"human-in-the-loop" design choice is worth stating explicitly in your
project report — it's a defensible engineering decision, not a shortcut.

Every scan (successful or not) is logged to `receipt_scans` for the audit
trail / admin panel, regardless of whether the user goes on to save it.
"""
import io
import os
import re
from datetime import datetime, date
from typing import Optional

import pytesseract

# Tell pytesseract exactly where Tesseract is installed
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from PIL import Image, ImageOps, ImageFilter
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/ocr", tags=["ocr"])

MAX_FILE_SIZE_MB = 8
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

# Keyword -> category name. Matched against the merchant line (case-insensitive).
# Category *names* are looked up against whatever is seeded in the DB, so this
# stays correct even if you edit database/schema.sql's category list later.
CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "restaurant", "cafe", "coffee", "pizza", "food", "kitchen", "diner",
        "bakery", "bar", "grill", "eatery", "swiggy", "zomato", "mcdonald",
        "starbucks", "dominos", "kfc", "burger",
    ],
    "Transport": ["uber", "ola", "taxi", "cab", "fuel", "petrol", "diesel", "metro", "parking", "fastag"],
    "Shopping": ["mart", "store", "shop", "retail", "amazon", "flipkart", "mall", "supermarket", "grocery"],
    "Utilities": ["electricity", "water bill", "gas bill", "broadband", "wifi", "recharge", "utility"],
    "Health": ["pharmacy", "hospital", "clinic", "medical", "chemist", "diagnostic", "medicine"],
    "Entertainment": ["cinema", "movie", "theatre", "netflix", "spotify", "multiplex", "pvr", "inox"],
    "Education": ["school", "college", "university", "tuition", "course", "books", "academy"],
}

# Matches amounts like: 1234.56  1,234.56  Rs. 1234  $12.34  INR 500
_AMOUNT_RE = re.compile(r"(?:rs\.?|inr|\$|usd)?\s*([0-9]{1,3}(?:[,.][0-9]{2,3})*(?:\.[0-9]{2})?)", re.IGNORECASE)
_TOTAL_LINE_RE = re.compile(r"(grand\s*total|total\s*amount|total|amount\s*due|balance\s*due|net\s*payable)", re.IGNORECASE)
_DATE_PATTERNS = [
    (re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b"), "dmy"),
    (re.compile(r"\b(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})\b"), "ymd"),
]


def _preprocess(image_bytes: bytes) -> Image.Image:
    """Light preprocessing improves Tesseract accuracy a lot on phone-camera receipts:
    grayscale -> autocontrast -> mild sharpen -> upscale if the photo is small."""
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("L")  # grayscale
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)
    if img.width < 1000:
        scale = 1000 / img.width
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    return img


def _extract_amount(text: str) -> Optional[float]:
    """Prefer the number on a line that says TOTAL/AMOUNT DUE/etc; fall back to the
    largest plausible currency number anywhere on the receipt."""
    lines = text.splitlines()
    candidates_on_total_lines = []
    all_candidates = []

    for line in lines:
        matches = _AMOUNT_RE.findall(line)
        for m in matches:
            cleaned = m.replace(",", "")
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


def _extract_date(text: str) -> Optional[date]:
    today = date.today()
    for pattern, order in _DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        try:
            if order == "dmy":
                d, mo, y = m.groups()
            else:
                y, mo, d = m.groups()
            y = int(y)
            if y < 100:
                y += 2000
            candidate = date(y, int(mo), int(d))
            if candidate.year >= 2000 and candidate <= today:
                return candidate
        except ValueError:
            continue
    return None


def _extract_merchant(text: str) -> Optional[str]:
    """Receipts almost always print the merchant/store name as one of the first
    non-empty lines, in the largest font on the page. We approximate that by
    taking the first line that looks like a name (mostly letters, reasonable length)."""
    for line in text.splitlines()[:8]:
        cleaned = line.strip()
        if 2 <= len(cleaned) <= 40 and sum(c.isalpha() for c in cleaned) >= max(2, len(cleaned) // 2):
            return cleaned
    return None


def _suggest_category(db: Session, merchant: Optional[str], raw_text: str):
    haystack = f"{merchant or ''} {raw_text}".lower()
    for category_name, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in haystack for kw in keywords):
            cat = db.query(models.Category).filter(models.Category.name == category_name).first()
            if cat:
                return cat
    # Fallback: generic "Shopping" if it exists, else the first non-income category
    fallback = (
        db.query(models.Category).filter(models.Category.name == "Shopping").first()
        or db.query(models.Category).filter(models.Category.is_income == False).first()
    )
    return fallback


@router.post("/scan-receipt", response_model=schemas.ReceiptScanOut)
async def scan_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Upload a JPEG, PNG, or WebP photo of the receipt.")

    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {MAX_FILE_SIZE_MB}MB).")

    try:
        image = _preprocess(raw_bytes)
        raw_text = pytesseract.image_to_string(image)
    except Exception as exc:  # pytesseract / PIL failures -> a clean 422, never a 500
        raise HTTPException(status_code=422, detail=f"Could not read this image: {exc}")

    amount = _extract_amount(raw_text)
    merchant = _extract_merchant(raw_text)
    parsed_date = _extract_date(raw_text) or date.today()
    category = _suggest_category(db, merchant, raw_text)

    # crude confidence heuristic: how many of the 3 key fields did we actually find?
    found = sum(x is not None for x in [amount, merchant])
    confidence = round((found / 2) * (0.9 if amount and merchant else 0.5), 2) if raw_text.strip() else 0.0

    scan = models.ReceiptScan(
        user_id=current_user.id,
        original_filename=file.filename,
        raw_text=raw_text[:4000],
        parsed_amount=amount,
        parsed_merchant=merchant,
        parsed_date=parsed_date,
        suggested_category_id=category.id if category else None,
        confidence=confidence,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    return schemas.ReceiptScanOut(
        scan_id=scan.id,
        raw_text=raw_text,
        parsed_amount=amount,
        parsed_merchant=merchant,
        parsed_date=parsed_date,
        suggested_category_id=category.id if category else None,
        suggested_category_name=category.name if category else None,
        confidence=confidence,
    )


@router.post("/scans/{scan_id}/link/{transaction_id}")
def link_scan_to_transaction(
    scan_id: int,
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Called after the frontend saves the confirmed transaction, so the audit
    trail (and admin panel) can show which transactions originated from a scan."""
    scan = db.query(models.ReceiptScan).filter(
        models.ReceiptScan.id == scan_id, models.ReceiptScan.user_id == current_user.id
    ).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    txn = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id, models.Transaction.user_id == current_user.id
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    scan.resulting_transaction_id = txn.id
    db.commit()
    return {"ok": True}


@router.get("/scans/history")
def scan_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    scans = (
        db.query(models.ReceiptScan)
        .filter(models.ReceiptScan.user_id == current_user.id)
        .order_by(models.ReceiptScan.created_at.desc())
        .limit(25)
        .all()
    )
    return [
        {
            "id": s.id,
            "original_filename": s.original_filename,
            "parsed_amount": s.parsed_amount,
            "parsed_merchant": s.parsed_merchant,
            "confidence": s.confidence,
            "resulting_transaction_id": s.resulting_transaction_id,
            "created_at": s.created_at,
        }
        for s in scans
    ]

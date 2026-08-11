"""
Phase 5: AI Integration. Turns the same numbers already on the dashboard into
plain-language savings advice via GPT.

Works without an API key too: if OPENAI_API_KEY isn't set, falls back to a
simple rule-based tip generator so the endpoint (and your demo) never breaks —
just swap in a real key when you're ready to show the "real" AI version.
"""
import os
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

import models, schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/insights", tags=["ai-insights"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _build_summary(db: Session, user_id: int) -> dict:
    total_spent = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
        .join(models.Category)
        .filter(models.Transaction.user_id == user_id, models.Category.is_income == False)
        .scalar()
    )
    total_income = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
        .join(models.Category)
        .filter(models.Transaction.user_id == user_id, models.Category.is_income == True)
        .scalar()
    )
    by_category = (
        db.query(models.Category.name, func.sum(models.Transaction.amount))
        .join(models.Transaction, models.Transaction.category_id == models.Category.id)
        .filter(models.Transaction.user_id == user_id, models.Category.is_income == False)
        .group_by(models.Category.name)
        .order_by(func.sum(models.Transaction.amount).desc())
        .all()
    )
    return {
        "total_spent": float(total_spent),
        "total_income": float(total_income),
        "top_categories": [{"category": c, "amount": float(a)} for c, a in by_category[:5]],
    }


def _fallback_tips(summary: dict) -> List[str]:
    """Rule-based backup used when no OpenAI key is configured."""
    tips = []
    if summary["total_income"] and summary["total_spent"] > 0.8 * summary["total_income"]:
        tips.append("You're spending over 80% of your income this period — worth tightening one category.")
    if summary["top_categories"]:
        top = summary["top_categories"][0]
        tips.append(f"'{top['category']}' is your biggest expense at {top['amount']:.0f} — look for one cut there.")
    savings = summary["total_income"] - summary["total_spent"]
    if savings > 0:
        tips.append(f"You saved {savings:.0f} this period. Consider auto-moving it to a savings goal.")
    else:
        tips.append("You spent more than you earned this period — review upcoming fixed costs.")
    return tips[:3]


def _generate_with_openai(summary: dict) -> List[str]:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = (
        "You are a concise personal finance assistant. Given this user's spending summary as JSON, "
        "give exactly 3 short, specific, actionable savings tips (one sentence each, no preamble):\n\n"
        f"{json.dumps(summary)}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250,
    )
    text = response.choices[0].message.content
    # Split into up to 3 lines/tips regardless of how the model formats them
    lines = [l.strip("-• ").strip() for l in text.split("\n") if l.strip()]
    return lines[:3] if lines else [text]


@router.post("/ai-advice", response_model=List[schemas.AIAdviceOut])
def generate_ai_advice(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    summary = _build_summary(db, current_user.id)

    if OPENAI_API_KEY:
        tips = _generate_with_openai(summary)
        kind = "ai-generated"
    else:
        tips = _fallback_tips(summary)
        kind = "rule-based-fallback"

    saved = []
    for tip in tips:
        suggestion = models.AISuggestion(user_id=current_user.id, kind=kind, message=tip)
        db.add(suggestion)
        saved.append(suggestion)
    db.commit()
    for s in saved:
        db.refresh(s)
    return saved


@router.get("/ai-advice", response_model=List[schemas.AIAdviceOut])
def get_ai_advice_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return (
        db.query(models.AISuggestion)
        .filter(models.AISuggestion.user_id == current_user.id)
        .order_by(models.AISuggestion.created_at.desc())
        .limit(10)
        .all()
    )

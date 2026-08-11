from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

import models, schemas
from database import get_db
from auth import get_current_user
from ml_service import forecast_next_month

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/forecast", response_model=schemas.ForecastOut)
def get_forecast(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    rows = (
        db.query(
           func.to_char(models.Transaction.txn_date, "YYYY-MM").label("month"),
            func.sum(models.Transaction.amount).label("total"),
        )
        .filter(models.Transaction.user_id == current_user.id)
        .group_by("month")
        .order_by("month")
        .all()
    )
    totals = [r.total for r in rows]
    predicted = forecast_next_month(totals)

    today = date.today()
    next_month = today.month % 12 + 1
    next_year = today.year + (1 if today.month == 12 else 0)
    label = f"{next_year}-{next_month:02d}"

    return {"month": label, "predicted_spend": round(predicted, 2)}


@router.get("/fraud-alerts")
def get_fraud_alerts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    logs = (
        db.query(models.FraudLog)
        .filter(models.FraudLog.user_id == current_user.id)
        .order_by(models.FraudLog.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": l.id,
            "transaction_id": l.transaction_id,
            "score": l.score,
            "reason": l.reason,
            "reviewed": l.reviewed,
            "created_at": l.created_at,
        }
        for l in logs
    ]


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """One call that feeds the whole dashboard header: totals + category breakdown."""
    total_spent = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
        .join(models.Category)
        .filter(models.Transaction.user_id == current_user.id, models.Category.is_income == False)
        .scalar()
    )
    total_income = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
        .join(models.Category)
        .filter(models.Transaction.user_id == current_user.id, models.Category.is_income == True)
        .scalar()
    )
    by_category = (
        db.query(models.Category.name, func.sum(models.Transaction.amount))
        .join(models.Transaction, models.Transaction.category_id == models.Category.id)
        .filter(models.Transaction.user_id == current_user.id, models.Category.is_income == False)
        .group_by(models.Category.name)
        .all()
    )
    flagged_count = (
        db.query(func.count(models.Transaction.id))
        .filter(models.Transaction.user_id == current_user.id, models.Transaction.is_flagged == True)
        .scalar()
    )

    return {
        "total_spent": float(total_spent),
        "total_income": float(total_income),
        "savings": float(total_income) - float(total_spent),
        "by_category": [{"category": name, "amount": float(amt)} for name, amt in by_category],
        "flagged_transactions": flagged_count,
    }

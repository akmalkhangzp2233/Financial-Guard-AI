from datetime import date
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import get_current_user
from ml_service import forecast_next_month


router = APIRouter(prefix="/insights", tags=["insights"])
logger = logging.getLogger(__name__)


# --------------------------------------------------
# Fraud risk classification
# --------------------------------------------------

def get_risk_level(score: float) -> str:
    """
    Assign a provisional risk label from the anomaly score.

    These thresholds are illustrative. An anomaly score is
    not a calibrated probability that a transaction is fraud.
    """
    if score <= -0.10:
        return "High"

    if score < 0:
        return "Medium"

    return "Low"


def serialize_fraud_alert(alert: models.FraudLog) -> dict:
    """Convert a FraudLog database record into an API response."""
    score = float(alert.score)

    return {
        "id": alert.id,
        "transaction_id": alert.transaction_id,
        "score": score,
        "risk_level": get_risk_level(score),
        "reason": alert.reason or "Unusual transaction pattern detected.",
        "reviewed": bool(alert.reviewed),
        "created_at": alert.created_at,
    }


# --------------------------------------------------
# Spending forecast
# --------------------------------------------------

@router.get("/forecast", response_model=schemas.ForecastOut)
def get_forecast(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Forecast next month's spending for the signed-in user."""

    # SQLite-compatible date formatting.
    rows = (
        db.query(
            func.strftime(
                "%Y-%m",
                models.Transaction.txn_date,
            ).label("month"),
            func.sum(
                models.Transaction.amount,
            ).label("total"),
        )
        .filter(
            models.Transaction.user_id == current_user.id,
        )
        .group_by("month")
        .order_by("month")
        .all()
    )

    totals = [
        float(row.total or 0)
        for row in rows
    ]

    try:
        predicted = forecast_next_month(totals)
    except (ValueError, TypeError) as exc:
        logger.warning(
            "Unable to calculate spending forecast: %s",
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Unable to calculate a forecast from the "
                "available transaction data."
            ),
        ) from exc

    today = date.today()
    next_month = today.month % 12 + 1
    next_year = today.year + (1 if today.month == 12 else 0)

    return {
        "month": f"{next_year}-{next_month:02d}",
        "predicted_spend": round(float(predicted), 2),
    }


# --------------------------------------------------
# Fraud alerts
# --------------------------------------------------

@router.get("/fraud-alerts")
def get_fraud_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return the latest 20 fraud alerts belonging to the signed-in user."""

    logs = (
        db.query(models.FraudLog)
        .filter(
            models.FraudLog.user_id == current_user.id,
        )
        .order_by(
            models.FraudLog.created_at.desc(),
            models.FraudLog.id.desc(),
        )
        .limit(20)
        .all()
    )

    return [
        serialize_fraud_alert(alert)
        for alert in logs
    ]


@router.patch(
    "/fraud-alerts/{alert_id}/review",
    status_code=status.HTTP_200_OK,
)
def mark_fraud_alert_reviewed(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Mark an alert belonging to the signed-in user as reviewed."""

    alert = (
        db.query(models.FraudLog)
        .filter(
            models.FraudLog.id == alert_id,
            models.FraudLog.user_id == current_user.id,
        )
        .first()
    )

    # Avoid revealing whether an alert belongs to another user.
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fraud alert not found.",
        )

    if not alert.reviewed:
        try:
            alert.reviewed = True
            db.commit()
            db.refresh(alert)
        except Exception as exc:
            db.rollback()
            logger.exception(
                "Failed to mark fraud alert %s as reviewed.",
                alert_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to update the alert. Please try again.",
            ) from exc

    return {
        "message": "Fraud alert marked as reviewed.",
        "alert": serialize_fraud_alert(alert),
    }


# --------------------------------------------------
# Dashboard summary
# --------------------------------------------------

@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return spending, income, savings, and category totals."""

    total_spent = (
        db.query(
            func.coalesce(
                func.sum(models.Transaction.amount),
                0,
            )
        )
        .join(
            models.Category,
            models.Transaction.category_id == models.Category.id,
        )
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Category.is_income.is_(False),
        )
        .scalar()
    )

    total_income = (
        db.query(
            func.coalesce(
                func.sum(models.Transaction.amount),
                0,
            )
        )
        .join(
            models.Category,
            models.Transaction.category_id == models.Category.id,
        )
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Category.is_income.is_(True),
        )
        .scalar()
    )

    by_category = (
        db.query(
            models.Category.name,
            func.sum(
                models.Transaction.amount,
            ).label("amount"),
        )
        .join(
            models.Transaction,
            models.Transaction.category_id == models.Category.id,
        )
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Category.is_income.is_(False),
        )
        .group_by(models.Category.name)
        .order_by(models.Category.name)
        .all()
    )

    flagged_count = (
        db.query(
            func.count(models.Transaction.id),
        )
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.is_flagged.is_(True),
        )
        .scalar()
    )

    spent = float(total_spent or 0)
    income = float(total_income or 0)

    return {
        "total_spent": spent,
        "total_income": income,
        "savings": income - spent,
        "by_category": [
            {
                "category": name,
                "amount": float(amount or 0),
            }
            for name, amount in by_category
        ],
        "flagged_transactions": int(flagged_count or 0),
    }
"""
Phase: Power BI / Reporting.

SQLite has no native Power BI connector, so the practical path for a student
project is: expose clean CSV endpoints -> Power BI's "Web" data source ->
point Power BI at these URLs directly (Get Data -> Web -> paste the URL +
your bearer token in the request header). This works identically whether
you're on SQLite (dev) or Postgres/MySQL (deployed) — you never have to
change your Power BI report when you switch databases.

If you DO migrate to Postgres/MySQL for deployment (recommended — see
DEPLOYMENT.md), you can alternatively point Power BI's native database
connector straight at `monthly_category_spend` (the view in
database/schema.sql) instead of using these endpoints. Keep both options in
your report: it shows you understood the trade-off, not just followed one path.
"""
import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import models
from database import get_db
from auth import get_current_user, get_current_admin

router = APIRouter(prefix="/reports", tags=["reports"])


def _csv_response(rows: list[dict], filename: str) -> StreamingResponse:
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/my-transactions.csv")
def export_my_transactions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """A single user's own transactions — safe for any logged-in user (feeds a personal
    Power BI / Excel report, or just a downloadable statement)."""
    rows = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.txn_date)
        .all()
    )
    data = [
        {
            "transaction_id": t.id,
            "date": t.txn_date,
            "category": t.category.name if t.category else "",
            "amount": t.amount,
            "merchant": t.merchant or "",
            "is_flagged": t.is_flagged,
        }
        for t in rows
    ]
    return _csv_response(data, "finguard_my_transactions.csv")


@router.get("/export/all-transactions.csv")
def export_all_transactions(db: Session = Depends(get_db), _admin: models.User = Depends(get_current_admin)):
    """Admin-only: the full transactions table across every user — this is the feed
    Power BI's platform-wide dashboards (Phase 7 of the roadmap) are built from."""
    rows = db.query(models.Transaction).order_by(models.Transaction.txn_date).all()
    data = [
        {
            "transaction_id": t.id,
            "user_id": t.user_id,
            "user_email": t.user.email if t.user else "",
            "date": t.txn_date,
            "category": t.category.name if t.category else "",
            "amount": t.amount,
            "merchant": t.merchant or "",
            "is_flagged": t.is_flagged,
            "fraud_score": t.fraud_score,
        }
        for t in rows
    ]
    return _csv_response(data, "finguard_all_transactions.csv")


@router.get("/export/monthly-summary.csv")
def export_monthly_summary(db: Session = Depends(get_db), _admin: models.User = Depends(get_current_admin)):
    """Pre-aggregated month x category totals — mirrors the `monthly_category_spend`
    SQL view, as a ready-to-import CSV for the Power BI matrix/heatmap visual."""
    from sqlalchemy import func
    rows = (
        db.query(
            func.strftime("%Y-%m", models.Transaction.txn_date).label("month"),
            models.Category.name.label("category"),
            func.sum(models.Transaction.amount).label("total"),
        )
        .join(models.Category, models.Transaction.category_id == models.Category.id)
        .filter(models.Category.is_income == False)
        .group_by("month", models.Category.name)
        .order_by("month")
        .all()
    )
    data = [{"month": r.month, "category": r.category, "total_spent": float(r.total)} for r in rows]
    return _csv_response(data, "finguard_monthly_summary.csv")

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date

import models, schemas
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("/", response_model=schemas.BudgetOut)
def upsert_budget(
    payload: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id,
        models.Budget.category_id == payload.category_id,
        models.Budget.month == payload.month,
    ).first()

    if existing:
        existing.limit_amount = payload.limit_amount

        db.commit()
        db.refresh(existing)

        return existing

    budget = models.Budget(
        user_id=current_user.id,
        **payload.model_dump()
    )

    db.add(budget)
    db.commit()
    db.refresh(budget)

    return budget


@router.get("/", response_model=List[schemas.BudgetOut])
def list_budgets(
    month: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id
    )

    if month:
        q = q.filter(models.Budget.month == month)

    return q.all()


@router.get("/vs-actual")
def budget_vs_actual(
    month: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Returns budget vs actual spending for each category.

    The previous version used SQLite's strftime() function.
    Render uses PostgreSQL, where strftime() does not exist.

    Instead, we convert YYYY-MM into a date range:
        >= first day of month
        < first day of next month

    This works with both SQLite and PostgreSQL.
    """

    budgets = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id,
        models.Budget.month == month,
    ).all()

    # Safely parse YYYY-MM
    try:
        year, month_number = map(int, month.split("-"))

        if month_number < 1 or month_number > 12:
            raise ValueError

        start_date = date(year, month_number, 1)

        if month_number == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month_number + 1, 1)

    except (ValueError, TypeError):
        return []

    result = []

    for budget in budgets:

        spent = (
            db.query(
                func.coalesce(
                    func.sum(models.Transaction.amount),
                    0
                )
            )
            .filter(
                models.Transaction.user_id == current_user.id,
                models.Transaction.category_id == budget.category_id,

                # IMPORTANT:
                # No strftime() here.
                # This works with PostgreSQL AND SQLite.
                models.Transaction.txn_date >= start_date,
                models.Transaction.txn_date < end_date,
            )
            .scalar()
        )

        result.append(
            {
                "category_id": budget.category_id,
                "category_name": budget.category.name,
                "limit": budget.limit_amount,
                "spent": float(spent or 0),
            }
        )

    return result

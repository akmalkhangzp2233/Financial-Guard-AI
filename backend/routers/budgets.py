from datetime import date
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from sqlalchemy import func

import models
import schemas

from database import get_db
from auth import get_current_user


router = APIRouter(
    prefix="/budgets",
    tags=["budgets"],
)


# ============================================================
# HELPER
# ============================================================

def _month_date_range(month: str):
    """
    Convert YYYY-MM into a start date and exclusive end date.

    Example:

        2026-08

    becomes:

        start = 2026-08-01
        end   = 2026-09-01

    This works with both SQLite and PostgreSQL.
    """

    try:

        year, month_number = map(
            int,
            month.split("-"),
        )

        if month_number < 1 or month_number > 12:
            raise ValueError

        start_date = date(
            year,
            month_number,
            1,
        )

        if month_number == 12:

            end_date = date(
                year + 1,
                1,
                1,
            )

        else:

            end_date = date(
                year,
                month_number + 1,
                1,
            )

        return start_date, end_date

    except (ValueError, TypeError):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid month format. "
                "Use YYYY-MM."
            ),
        )


# ============================================================
# CREATE / UPDATE BUDGET
# ============================================================

@router.post(
    "/",
    response_model=schemas.BudgetOut,
)
def upsert_budget(
    payload: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):

    existing = (
        db.query(models.Budget)
        .filter(
            models.Budget.user_id
            == current_user.id,

            models.Budget.category_id
            == payload.category_id,

            models.Budget.month
            == payload.month,
        )
        .first()
    )

    # --------------------------------------------------------
    # Update existing budget
    # --------------------------------------------------------

    if existing:

        existing.limit_amount = (
            payload.limit_amount
        )

        db.commit()

        db.refresh(existing)

        return existing

    # --------------------------------------------------------
    # Create new budget
    # --------------------------------------------------------

    budget = models.Budget(
        user_id=current_user.id,
        **payload.model_dump(),
    )

    db.add(budget)

    db.commit()

    db.refresh(budget)

    return budget


# ============================================================
# LIST BUDGETS
# ============================================================

@router.get(
    "/",
    response_model=List[schemas.BudgetOut],
)
def list_budgets(
    month: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):

    query = (
        db.query(models.Budget)
        .filter(
            models.Budget.user_id
            == current_user.id
        )
    )

    if month:

        query = query.filter(
            models.Budget.month == month
        )

    return query.all()


# ============================================================
# BUDGET VS ACTUAL
# ============================================================

@router.get("/vs-actual")
def budget_vs_actual(
    month: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Returns budget limit vs actual spending for each
    budget category.

    IMPORTANT:
    This uses a date range instead of SQLite's strftime().
    Therefore it works with PostgreSQL on Render as well
    as SQLite locally.
    """

    # --------------------------------------------------------
    # Validate month and create date range
    # --------------------------------------------------------

    start_date, end_date = _month_date_range(month)

    # --------------------------------------------------------
    # Get user's budgets for requested month
    # --------------------------------------------------------

    budgets = (
        db.query(models.Budget)
        .filter(
            models.Budget.user_id
            == current_user.id,

            models.Budget.month
            == month,
        )
        .all()
    )

    result = []

    # --------------------------------------------------------
    # Calculate actual spending
    # --------------------------------------------------------

    for budget in budgets:

        spent = (
            db.query(
                func.coalesce(
                    func.sum(
                        models.Transaction.amount
                    ),
                    0,
                )
            )
            .filter(
                models.Transaction.user_id
                == current_user.id,

                models.Transaction.category_id
                == budget.category_id,

                models.Transaction.txn_date
                >= start_date,

                models.Transaction.txn_date
                < end_date,
            )
            .scalar()
        )

        result.append(
            {
                "category_id": budget.category_id,

                "category_name": (
                    budget.category.name
                    if budget.category
                    else "Unknown"
                ),

                "limit": float(
                    budget.limit_amount
                ),

                "spent": float(
                    spent or 0
                ),
            }
        )

    return result

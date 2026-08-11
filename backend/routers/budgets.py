from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

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

    budget = models.Budget(user_id=current_user.id, **payload.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get("/", response_model=List[schemas.BudgetOut])
def list_budgets(month: str = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    q = db.query(models.Budget).filter(models.Budget.user_id == current_user.id)
    if month:
        q = q.filter(models.Budget.month == month)
    return q.all()


@router.get("/vs-actual")
def budget_vs_actual(month: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Powers the 'Budget' dashboard chart: limit vs. what was actually spent, per category."""
    budgets = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id, models.Budget.month == month
    ).all()

    result = []
    for b in budgets:
        spent = (
            db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
            .filter(
                models.Transaction.user_id == current_user.id,
                models.Transaction.category_id == b.category_id,
                func.strftime("%Y-%m", models.Transaction.txn_date) == month,
            )
            .scalar()
        )
        result.append({
            "category_id": b.category_id,
            "category_name": b.category.name,
            "limit": b.limit_amount,
            "spent": float(spent),
        })
    return result

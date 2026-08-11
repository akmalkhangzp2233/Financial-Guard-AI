from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from auth import get_current_user
from ml_service import score_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=schemas.TransactionOut)
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    txn = models.Transaction(user_id=current_user.id, **payload.model_dump())

    # Run every new transaction through the fraud model before saving.
    score, is_flagged, reason = score_transaction(db, current_user.id, payload.amount, payload.category_id)
    txn.fraud_score = score
    txn.is_flagged = is_flagged

    db.add(txn)
    db.commit()
    db.refresh(txn)

    if is_flagged:
        db.add(models.FraudLog(transaction_id=txn.id, user_id=current_user.id, score=score, reason=reason))
        db.commit()

    return txn


@router.get("/", response_model=List[schemas.TransactionOut])
def list_transactions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.txn_date.desc())
        .all()
    )


@router.delete("/{txn_id}")
def delete_transaction(txn_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    txn = db.query(models.Transaction).filter(
        models.Transaction.id == txn_id, models.Transaction.user_id == current_user.id
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(txn)
    db.commit()
    return {"ok": True}

"""
Phase: Admin Panel.

Everything here requires get_current_admin (see auth.py) — a non-admin JWT
gets a clean 403, not a 404 (we don't need to hide that the routes exist;
FastAPI's own /docs already lists them).

The first user ever registered on a fresh database is auto-promoted to admin
(see routers/auth.py::register), so there's always exactly one admin account
ready for your demo without any manual DB editing.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

import models, schemas
from database import get_db
from auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=schemas.AdminStatsOut)
def platform_stats(db: Session = Depends(get_db), _admin: models.User = Depends(get_current_admin)):
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    return schemas.AdminStatsOut(
        total_users=db.query(func.count(models.User.id)).scalar() or 0,
        active_users=db.query(func.count(models.User.id)).filter(models.User.is_active == True).scalar() or 0,
        total_transactions=db.query(func.count(models.Transaction.id)).scalar() or 0,
        total_flagged=db.query(func.count(models.Transaction.id)).filter(models.Transaction.is_flagged == True).scalar() or 0,
        total_volume=float(db.query(func.coalesce(func.sum(models.Transaction.amount), 0)).scalar() or 0),
        total_receipt_scans=db.query(func.count(models.ReceiptScan.id)).scalar() or 0,
        signups_last_7_days=db.query(func.count(models.User.id)).filter(models.User.created_at >= seven_days_ago).scalar() or 0,
    )


@router.get("/users", response_model=List[schemas.AdminUserOut])
def list_users(db: Session = Depends(get_db), _admin: models.User = Depends(get_current_admin)):
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    out = []
    for u in users:
        txn_q = db.query(models.Transaction).filter(models.Transaction.user_id == u.id)
        out.append(
            schemas.AdminUserOut(
                id=u.id,
                full_name=u.full_name,
                email=u.email,
                is_admin=u.is_admin,
                is_active=u.is_active,
                created_at=u.created_at,
                transaction_count=txn_q.count(),
                total_spent=float(txn_q.with_entities(func.coalesce(func.sum(models.Transaction.amount), 0)).scalar() or 0),
                flagged_count=txn_q.filter(models.Transaction.is_flagged == True).count(),
            )
        )
    return out


@router.patch("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You can't deactivate your own account.")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@router.patch("/users/{user_id}/toggle-admin")
def toggle_user_admin(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You can't revoke your own admin access.")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = not user.is_admin
    db.commit()
    return {"id": user.id, "is_admin": user.is_admin}


@router.get("/transactions")
def list_all_transactions(
    flagged_only: bool = False,
    limit: int = 100,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_current_admin),
):
    q = db.query(models.Transaction).order_by(models.Transaction.created_at.desc())
    if flagged_only:
        q = q.filter(models.Transaction.is_flagged == True)
    rows = q.limit(min(limit, 500)).all()
    return [
        {
            "id": t.id,
            "user_id": t.user_id,
            "user_email": t.user.email if t.user else None,
            "amount": t.amount,
            "merchant": t.merchant,
            "category_id": t.category_id,
            "category_name": t.category.name if t.category else None,
            "txn_date": t.txn_date,
            "is_flagged": t.is_flagged,
            "fraud_score": t.fraud_score,
        }
        for t in rows
    ]


@router.get("/fraud-logs", response_model=List[schemas.AdminFraudLogOut])
def list_fraud_logs(
    reviewed: Optional[bool] = None,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_current_admin),
):
    q = db.query(models.FraudLog).order_by(models.FraudLog.created_at.desc())
    if reviewed is not None:
        q = q.filter(models.FraudLog.reviewed == reviewed)
    logs = q.limit(200).all()
    out = []
    for l in logs:
        user = db.query(models.User).filter(models.User.id == l.user_id).first()
        out.append(
            schemas.AdminFraudLogOut(
                id=l.id,
                transaction_id=l.transaction_id,
                user_id=l.user_id,
                user_email=user.email if user else "unknown",
                score=l.score,
                reason=l.reason,
                reviewed=l.reviewed,
                created_at=l.created_at,
            )
        )
    return out


@router.patch("/fraud-logs/{log_id}/review")
def mark_fraud_log_reviewed(log_id: int, db: Session = Depends(get_db), _admin: models.User = Depends(get_current_admin)):
    log = db.query(models.FraudLog).filter(models.FraudLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Fraud log not found")
    log.reviewed = True
    db.commit()
    return {"id": log.id, "reviewed": True}

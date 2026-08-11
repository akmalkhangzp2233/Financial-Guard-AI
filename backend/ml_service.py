"""
Thin wrapper the API calls into. Keeps FastAPI routers free of ML code and
lets you retrain/swap models without touching the API.
"""

import os
import math
import joblib
import numpy as np

from sqlalchemy.orm import Session
from sqlalchemy import func

import models as db_models

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")
FRAUD_MODEL_PATH = os.path.join(MODEL_DIR, "fraud_isolation_forest.pkl")
FORECAST_MODEL_PATH = os.path.join(MODEL_DIR, "expense_forecaster.pkl")

_fraud_model = None
_forecast_model = None


def _load_fraud_model():
    global _fraud_model
    if _fraud_model is None:
        if os.path.exists(FRAUD_MODEL_PATH):
            _fraud_model = joblib.load(FRAUD_MODEL_PATH)
        else:
            _fraud_model = None
    return _fraud_model


def _load_forecast_model():
    global _forecast_model
    if _forecast_model is None and os.path.exists(FORECAST_MODEL_PATH):
        _forecast_model = joblib.load(FORECAST_MODEL_PATH)
    return _forecast_model


def score_transaction(db: Session, user_id: int, amount: float, category_id: int):
    """
    Returns:
        (score, is_flagged, reason)
    """

    model = _load_fraud_model()

    avg_amount = (
        db.query(func.avg(db_models.Transaction.amount))
        .filter(db_models.Transaction.user_id == user_id)
        .scalar()
    ) or amount

    mean_square = (
        db.query(
            func.coalesce(
                func.avg(
                    db_models.Transaction.amount *
                    db_models.Transaction.amount
                ),
                0,
            )
        )
        .filter(db_models.Transaction.user_id == user_id)
        .scalar()
    ) or 0

    variance = max(mean_square - (avg_amount ** 2), 0.0)
    std_amount = max(math.sqrt(variance), 1.0)

    if model is not None:
        features = np.array([[amount, category_id]])
        raw_score = model.decision_function(features)[0]
        prediction = model.predict(features)[0]

        is_flagged = prediction == -1
        score = float(raw_score)

        if is_flagged:
            reason = "Flagged by fraud detection model (unusual amount/category pattern)"
        else:
            reason = "Normal"

    else:
        z = (amount - avg_amount) / std_amount
        is_flagged = z > 3
        score = float(z)

        if is_flagged:
            reason = "Flagged: amount is a statistical outlier vs. your history"
        else:
            reason = "Normal"

    return score, is_flagged, reason


def forecast_next_month(monthly_totals: list[float]) -> float:
    """
    Predict next month's spending.
    """

    model = _load_forecast_model()

    if model is not None and len(monthly_totals) >= 3:
        window = np.array(monthly_totals[-3:]).reshape(1, -1)
        return float(model.predict(window)[0])

    if not monthly_totals:
        return 0.0

    recent = monthly_totals[-3:]
    weights = np.linspace(1, 2, len(recent))
    return float(np.average(recent, weights=weights))
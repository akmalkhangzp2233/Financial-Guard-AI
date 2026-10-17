"""
FinGuard AI - Machine Learning Service

Provides fraud anomaly detection and monthly spending forecasts.
Preserves existing function signatures for API compatibility.
"""

import logging
import math
import os
import warnings

import joblib
import numpy as np

from sqlalchemy import func
from sqlalchemy.orm import Session

import models as db_models


# =========================================================
# Configuration
# =========================================================

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "ml", "models")
)

FRAUD_MODEL_PATH = os.path.join(
    MODEL_DIR, "fraud_isolation_forest.pkl"
)

FORECAST_MODEL_PATH = os.path.join(
    MODEL_DIR, "expense_forecaster.pkl"
)

_fraud_model = None
_forecast_model = None

_fraud_load_attempted = False
_forecast_load_attempted = False

MIN_HISTORY_FOR_STATISTICS = 5
ANOMALY_Z_THRESHOLD = 3.0


# =========================================================
# Model Loading
# =========================================================

def _load_model(path: str, name: str):
    """Load a trained model and log any compatibility warnings."""

    if not os.path.isfile(path):
        logger.warning(
            "%s model not found at %s",
            name,
            path,
        )
        return None

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = joblib.load(path)

        for warning in caught:
            logger.warning(
                "%s model warning: %s",
                name,
                warning.message,
            )

        if not callable(getattr(model, "predict", None)):
            logger.error("%s model has no predict() method.", name)
            return None

        logger.info("%s model loaded successfully.", name)
        return model

    except Exception:
        logger.exception("Unable to load %s model.", name)
        return None


def _load_fraud_model():
    global _fraud_model, _fraud_load_attempted

    if not _fraud_load_attempted:
        _fraud_load_attempted = True

        model = _load_model(
            FRAUD_MODEL_PATH,
            "Fraud detection",
        )

        if model is not None:
            feature_count = getattr(
                model,
                "n_features_in_",
                None,
            )

            if feature_count is not None and feature_count != 2:
                logger.error(
                    "Fraud model expects %s features, but this "
                    "service supplies 2.",
                    feature_count,
                )
                model = None

            elif not callable(
                getattr(model, "decision_function", None)
            ):
                logger.error(
                    "Fraud model does not support decision_function()."
                )
                model = None

        _fraud_model = model

    return _fraud_model


def _load_forecast_model():
    global _forecast_model, _forecast_load_attempted

    if not _forecast_load_attempted:
        _forecast_load_attempted = True

        _forecast_model = _load_model(
            FORECAST_MODEL_PATH,
            "Spending forecast",
        )

    return _forecast_model


# =========================================================
# Risk Labels
# =========================================================

def get_risk_label(score: float, is_flagged: bool) -> str:
    """
    Return a display label without changing the existing API response.

    Isolation Forest decision scores and statistical z-scores have
    different meanings. Therefore, labels should not be inferred
    from the raw score alone.
    """

    if not is_flagged:
        return "Low"

    return "High"


# =========================================================
# Input Validation
# =========================================================

def _validate_transaction(
    user_id: int,
    amount: float,
    category_id: int,
):
    try:
        user_id = int(user_id)
        amount = float(amount)
        category_id = int(category_id)

    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            "User ID, amount, and category ID must be numeric."
        ) from exc

    if user_id <= 0:
        raise ValueError("User ID must be positive.")

    if category_id <= 0:
        raise ValueError("Category ID must be positive.")

    if not math.isfinite(amount) or amount < 0:
        raise ValueError(
            "Transaction amount must be finite and non-negative."
        )

    return user_id, amount, category_id


# =========================================================
# Historical Spending Statistics
# =========================================================

def _get_user_statistics(
    db: Session,
    user_id: int,
):
    """Calculate statistics using this user's transaction history."""

    transaction = db_models.Transaction

    result = (
        db.query(
            func.count(transaction.id),
            func.avg(transaction.amount),
            func.avg(
                transaction.amount * transaction.amount
            ),
        )
        .filter(transaction.user_id == user_id)
        .one()
    )

    count, average, mean_square = result

    count = int(count or 0)

    if count == 0 or average is None or mean_square is None:
        return count, None, None

    average = float(average)
    mean_square = float(mean_square)

    variance = max(
        mean_square - average**2,
        0.0,
    )

    standard_deviation = max(
        math.sqrt(variance),
        1.0,
    )

    return count, average, standard_deviation


# =========================================================
# Statistical Fallback
# =========================================================

def _statistical_fraud_score(
    db: Session,
    user_id: int,
    amount: float,
):
    """
    Flag unusual amounts relative to the user's historical spending.

    This fallback is a simple statistical detector, not a trained
    fraud classifier.
    """

    count, average, standard_deviation = _get_user_statistics(
        db,
        user_id,
    )

    if (
        count < MIN_HISTORY_FOR_STATISTICS
        or average is None
        or standard_deviation is None
    ):
        return (
            0.0,
            False,
            "Insufficient transaction history for statistical detection",
        )

    z_score = (amount - average) / standard_deviation

    is_flagged = abs(z_score) > ANOMALY_Z_THRESHOLD

    if is_flagged and z_score > 0:
        reason = (
            "Potential anomaly: amount is unusually high "
            "compared with your spending history"
        )
    elif is_flagged:
        reason = (
            "Potential anomaly: amount is unusually low "
            "compared with your spending history"
        )
    else:
        reason = "No statistical anomaly detected"

    return float(z_score), is_flagged, reason


# =========================================================
# Fraud Detection
# =========================================================

def score_transaction(
    db: Session,
    user_id: int,
    amount: float,
    category_id: int,
):
    """
    Returns:
        (score, is_flagged, reason)

    A flagged transaction is an anomaly for review, not confirmed fraud.
    """

    user_id, amount, category_id = _validate_transaction(
        user_id,
        amount,
        category_id,
    )

    model = _load_fraud_model()

    if model is not None:
        try:
            features = np.asarray(
                [[amount, category_id]],
                dtype=np.float64,
            )

            prediction = int(model.predict(features)[0])

            score = float(
                model.decision_function(features)[0]
            )

            if not math.isfinite(score):
                raise ValueError(
                    "Fraud model returned a non-finite score."
                )

            is_flagged = prediction == -1

            if is_flagged:
                reason = (
                    "Potential anomaly flagged by the fraud detection "
                    "model (unusual amount/category pattern)"
                )
            else:
                reason = "No anomaly detected by the fraud model"

            return score, is_flagged, reason

        except Exception:
            logger.exception(
                "Fraud model scoring failed; trying statistical fallback."
            )

    return _statistical_fraud_score(
        db,
        user_id,
        amount,
    )


# =========================================================
# Spending Forecast
# =========================================================

def forecast_next_month(
    monthly_totals: list[float],
) -> float:
    """Predict next month's spending using the trained model or fallback."""

    try:
        totals = [
            float(value)
            for value in monthly_totals
        ]

    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            "Monthly spending totals must be numeric."
        ) from exc

    if not all(math.isfinite(value) for value in totals):
        raise ValueError(
            "Monthly spending totals must be finite."
        )

    if any(value < 0 for value in totals):
        raise ValueError(
            "Monthly spending totals cannot be negative."
        )

    if not totals:
        return 0.0

    model = _load_forecast_model()

    if model is not None and len(totals) >= 3:
        try:
            features = np.asarray(
                totals[-3:],
                dtype=np.float64,
            ).reshape(1, -1)

            expected = getattr(
                model,
                "n_features_in_",
                None,
            )

            if expected is not None and expected != 3:
                raise ValueError(
                    f"Forecast model expects {expected} features; "
                    "this service supplies 3."
                )

            prediction = float(model.predict(features)[0])

            if not math.isfinite(prediction):
                raise ValueError(
                    "Forecast model returned an invalid prediction."
                )

            return max(prediction, 0.0)

        except Exception:
            logger.exception(
                "Forecast prediction failed; using weighted average."
            )

    recent = np.asarray(
        totals[-3:],
        dtype=np.float64,
    )

    weights = np.linspace(
        1.0,
        2.0,
        len(recent),
    )

    forecast = float(
        np.average(recent, weights=weights)
    )

    return max(forecast, 0.0)
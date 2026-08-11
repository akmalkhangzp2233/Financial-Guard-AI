"""
Trains a simple regression model that predicts next month's total spend from
the previous 3 months' totals. Deliberately simple (Linear Regression) so you
can explain every coefficient in your viva — swap in RandomForestRegressor or
a Prophet/LSTM model later for the "Savings Forecast" roadmap item once this
baseline works end-to-end.

Output: ml/models/expense_forecaster.pkl
"""
import os
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def generate_synthetic_monthly_series(n_users=300, n_months=6, seed=7):
    """
    Each row = one user's 3 preceding months -> the 4th month's actual spend.
    Base spend has a mild upward trend + noise, which is realistic for a
    student's or young professional's growing expenses.
    """
    rng = np.random.default_rng(seed)
    X, y = [], []
    for _ in range(n_users):
        base = rng.uniform(200, 800)
        trend = rng.uniform(-20, 40)
        series = [max(base + trend * m + rng.normal(0, 30), 0) for m in range(n_months)]
        for i in range(len(series) - 3):
            X.append(series[i:i + 3])
            y.append(series[i + 3])
    return np.array(X), np.array(y)


def train():
    X, y = generate_synthetic_monthly_series()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"Test MAE: {mae:.2f} (avg error in predicted monthly spend)")

    joblib.dump(model, os.path.join(MODEL_DIR, "expense_forecaster.pkl"))
    print(f"Saved model to {MODEL_DIR}/expense_forecaster.pkl")


if __name__ == "__main__":
    train()

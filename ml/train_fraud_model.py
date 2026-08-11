"""
Trains an Isolation Forest fraud detector on transaction (amount, category_id) pairs.

TWO WAYS TO USE THIS:
1. Quick start (what runs by default below): generates realistic synthetic
   transactions so your app works end-to-end immediately.
2. For a real final-year-project-grade model: download the Kaggle
   "Credit Card Fraud Detection" dataset (creditcard.csv, ~284k rows,
   https://www.kaggle.com/mlg-ulb/creditcardfraud), drop it in ml/data/,
   and swap in `load_kaggle_data()` below instead of `generate_synthetic_data()`.
   That dataset is pre-labeled (Class 0/1) so you can also report real
   precision/recall/AUC/F1 in your report — reviewers will ask for these.

Output: ml/models/fraud_isolation_forest.pkl
"""
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def generate_synthetic_data(n_normal=2000, n_fraud=60, n_categories=10, seed=42):
    """
    Normal transactions cluster in a realistic ₹/$ range per category.
    Fraud transactions are injected as amount outliers (very large or oddly
    precise amounts) — mimicking real card-fraud patterns for demo purposes.
    """
    rng = np.random.default_rng(seed)

    normal_amounts = rng.gamma(shape=2.0, scale=25, size=n_normal)  # right-skewed spend
    normal_categories = rng.integers(1, n_categories + 1, size=n_normal)

    fraud_amounts = rng.uniform(500, 5000, size=n_fraud)  # unusually large charges
    fraud_categories = rng.integers(1, n_categories + 1, size=n_fraud)

    amounts = np.concatenate([normal_amounts, fraud_amounts])
    categories = np.concatenate([normal_categories, fraud_categories])
    labels = np.concatenate([np.zeros(n_normal), np.ones(n_fraud)])  # 1 = fraud (for evaluation only)

    df = pd.DataFrame({"amount": amounts, "category_id": categories, "is_fraud": labels})
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def load_kaggle_data(path="ml/data/creditcard.csv"):
    """Use this instead of generate_synthetic_data() once you have the real dataset."""
    df = pd.read_csv(path)
    df = df.rename(columns={"Amount": "amount", "Class": "is_fraud"})
    df["category_id"] = 0  # Kaggle dataset has no category column; drop that feature or engineer one
    return df[["amount", "category_id", "is_fraud"]]


def train():
    df = generate_synthetic_data()
    X = df[["amount", "category_id"]].values

    # contamination = expected proportion of anomalies in the data (tune this to your dataset)
    model = IsolationForest(n_estimators=200, contamination=0.03, random_state=42)
    model.fit(X)

    joblib.dump(model, os.path.join(MODEL_DIR, "fraud_isolation_forest.pkl"))
    print(f"Saved model to {MODEL_DIR}/fraud_isolation_forest.pkl")

    # Quick sanity check against our synthetic labels (only possible because we know them here)
    preds = model.predict(X)  # -1 = anomaly, 1 = normal
    predicted_fraud = (preds == -1).astype(int)
    actual_fraud = df["is_fraud"].values
    tp = int(((predicted_fraud == 1) & (actual_fraud == 1)).sum())
    fp = int(((predicted_fraud == 1) & (actual_fraud == 0)).sum())
    fn = int(((predicted_fraud == 0) & (actual_fraud == 1)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    print(f"Sanity check on synthetic data — precision: {precision:.2f}, recall: {recall:.2f}")
    print("NOTE: replace with load_kaggle_data() + a train/test split for a report-worthy evaluation.")


if __name__ == "__main__":
    train()

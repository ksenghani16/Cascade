# training/train_classifier.py
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import sys, os

# Get the absolute path to the ml_service folder, no matter where this script is run from
ML_SERVICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml_service"))
sys.path.insert(0, ML_SERVICE_PATH)

print(f"Looking for embeddings.py in: {ML_SERVICE_PATH}")  # temporary debug line

from embeddings import embed_text
def build_feature_matrix(df):
    # Turn every ticket's text into an embedding vector...
    text_embeddings = np.array([embed_text(t) for t in df["text"]])
    # ...then attach the two numeric features alongside it.
    numeric = df[["account_age_days", "prior_tickets_30d"]].values
    return np.hstack([text_embeddings, numeric])
def train_and_save(df, out_path="storage/classifier.joblib"):
    X = build_feature_matrix(df)
    y = df["category"]

    # Simpler split: 80% to train+calibrate together, 20% held out as a true test set
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    base_model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)

    # cv=5 means: internally split X_train/y_train into 5 folds, train the
    # base model on 4 folds and calibrate on the 5th, rotating through all
    # 5 combinations. This does both training AND calibration in one call,
    # without needing to manually pre-fit the base model first.
    calibrated_model = CalibratedClassifierCV(base_model, method="isotonic", cv=5)
    calibrated_model.fit(X_train, y_train)

    preds = calibrated_model.predict(X_test)
    print(classification_report(y_test, preds))

    joblib.dump(calibrated_model, out_path)
    print(f"Saved calibrated classifier to {out_path}")
    return calibrated_model

if __name__ == "__main__":
    df = pd.read_csv("data/tickets.csv")
    train_and_save(df)
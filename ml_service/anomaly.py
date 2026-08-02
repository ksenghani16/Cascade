from sklearn.ensemble import IsolationForest
import numpy as np
import joblib

def fit_anomaly_model(df, out_path="../storage/anomaly_model.joblib"):
    features = df[["account_age_days", "prior_tickets_30d"]].values
    model = IsolationForest(n_estimators=150, contamination=0.03, random_state=42)
    model.fit(features)
    joblib.dump(model, out_path)

def check_anomaly(account_age_days: int, prior_tickets_30d: int,
                   model_path="../storage/anomaly_model.joblib"):
    model = joblib.load(model_path)
    x = np.array([[account_age_days, prior_tickets_30d]])
    prediction = model.predict(x)[0]
    score = model.decision_function(x)[0]
    return bool(prediction == -1), float(score)
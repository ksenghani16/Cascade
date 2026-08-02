import numpy as np
import hdbscan
import joblib
from sklearn.preprocessing import StandardScaler
from embeddings import embed_text

def fit_cluster_model(df, out_path="../storage/cluster_model.joblib"):
    text_embeddings = np.array([embed_text(t) for t in df["text"]])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(text_embeddings)

    clusterer = hdbscan.HDBSCAN(min_cluster_size=15, prediction_data=True)
    clusterer.fit(X_scaled)

    joblib.dump({"scaler": scaler, "clusterer": clusterer}, out_path)
    return clusterer

def check_novelty(ticket_text: str, model_path="../storage/cluster_model.joblib"):
    bundle = joblib.load(model_path)
    scaler, clusterer = bundle["scaler"], bundle["clusterer"]

    x = np.array([embed_text(ticket_text)])
    x_scaled = scaler.transform(x)

    labels, strengths = hdbscan.approximate_predict(clusterer, x_scaled)
    is_novel = labels[0] == -1
    return bool(is_novel), float(strengths[0])
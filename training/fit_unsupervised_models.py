import sys, os
import pandas as pd

ML_SERVICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml_service"))
sys.path.insert(0, ML_SERVICE_PATH)

from clustering import fit_cluster_model
from anomaly import fit_anomaly_model

df = pd.read_csv("data/tickets.csv")
fit_cluster_model(df)
fit_anomaly_model(df)
print("Both unsupervised models saved.")
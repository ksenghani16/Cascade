# ml_service/explain.py
import shap
import joblib
import numpy as np
from embeddings import embed_text

def explain_prediction(ticket_text: str, account_age_days: int, prior_tickets_30d: int,
                        model_path="ml_service/data/classifier.joblib"):
    model = joblib.load(model_path)
    underlying_model = model.calibrated_classifiers_[0].estimator
    explainer = shap.TreeExplainer(underlying_model)

    text_embedding = embed_text(ticket_text)
    x = np.array([text_embedding + [account_age_days, prior_tickets_30d]])
    shap_values = explainer.shap_values(x)

    # Text embeddings don't map to human-readable "words" directly through
    # SHAP this way — so for a portfolio explanation, focus SHAP reporting
    # on the two numeric features (account_age_days, prior_tickets_30d),
    # and note this limitation openly: "for the text-derived features, I'd
    # want a word-attribution method like SHAP's text explainer or LIME
    # in a production version."
    return shap_values
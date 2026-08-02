# ml_service/threshold_bandit.py
import numpy as np
import json
import os

THRESHOLD_CANDIDATES = {
    "billing": [0.75, 0.80, 0.85, 0.90],
    "technical": [0.70, 0.75, 0.80, 0.85],
    "account": [0.75, 0.80, 0.85, 0.90],
    "general": [0.60, 0.65, 0.70, 0.75],
}

STATE_FILE = "../storage/threshold_bandit_state.json"

def _load_state():
    if not os.path.exists(STATE_FILE):
        state = {
            category: {str(t): {"alpha": 1, "beta": 1} for t in thresholds}
            for category, thresholds in THRESHOLD_CANDIDATES.items()
        }
        _save_state(state)
        return state
    with open(STATE_FILE) as f:
        return json.load(f)

def _save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def choose_threshold(category: str) -> float:
    state = _load_state()
    options = state[category]
    samples = {t: np.random.beta(v["alpha"], v["beta"]) for t, v in options.items()}
    return float(max(samples, key=samples.get))

def record_threshold_outcome(category: str, threshold_used: float, ticket_was_reopened: bool):
    """Call this once you know whether an auto-replied ticket got reopened
    (a strong real-world signal the auto-reply didn't actually resolve it)."""
    state = _load_state()
    key = str(threshold_used)
    if not ticket_was_reopened:
        state[category][key]["alpha"] += 1   # good outcome
    else:
        state[category][key]["beta"] += 1     # bad outcome — auto-reply wasn't good enough
    _save_state(state)
# ml_service/bandit.py
import numpy as np
import json
import os
from reward import compute_reward

STRATEGIES = ["short_template", "llm_detailed_reply", "escalate_to_senior_agent"]
STATE_FILE = "../storage/bandit_state.json"

def _load_state():
    if not os.path.exists(STATE_FILE):
        state = {s: {"alpha": 1, "beta": 1} for s in STRATEGIES}
        _save_state(state)
        return state
    with open(STATE_FILE) as f:
        return json.load(f)

def _save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def choose_strategy():
    """Thompson Sampling: draw one 'how good is this option probably' guess
    per strategy, pick the highest. Early on this is noisy (lots of
    exploring); once one strategy clearly wins, it gets picked most often."""
    state = _load_state()
    samples = {s: np.random.beta(state[s]["alpha"], state[s]["beta"]) for s in STRATEGIES}
    return max(samples, key=samples.get)

def record_outcome(strategy: str, resolved_without_reopen: bool,
                    time_to_resolution_minutes: float, cost_incurred: float,
                    weights: dict = None):
    reward = compute_reward(resolved_without_reopen, time_to_resolution_minutes,
                             cost_incurred, weights)
    state = _load_state()
    if reward > 0:
        state[strategy]["alpha"] += reward
    else:
        state[strategy]["beta"] += abs(reward)
    _save_state(state)
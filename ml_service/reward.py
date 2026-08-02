# ml_service/reward.py

def compute_reward(resolved_without_reopen: bool, time_to_resolution_minutes: float,
                    cost_incurred: float, weights: dict = None) -> float:
    """
    weights lets you say what matters most right now, e.g.
      {"success": 1.0, "speed": 0.3, "cost": 0.2}
    means "not reopening matters most, but speed and cost still count."
    """
    if weights is None:
        weights = {"success": 1.0, "speed": 0.3, "cost": 0.2}

    success_term = 1.0 if resolved_without_reopen else -1.0
    speed_penalty = min(time_to_resolution_minutes / 120.0, 1.0)  # cap at 2 hours
    cost_penalty = min(cost_incurred / 2.0, 1.0)                    # cap at $2-equivalent

    return (
        weights["success"] * success_term
        - weights["speed"] * speed_penalty
        - weights["cost"] * cost_penalty
    )
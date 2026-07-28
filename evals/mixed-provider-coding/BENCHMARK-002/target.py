"""Small benchmark target: bounded receipt lifecycle helpers."""


def transition(current, event):
    """Return the next lifecycle state for a receipt attempt.

    Supported states are active, stale, abandoned, and complete. A replacement
    attempt starts active; an original attempt may be abandoned after stale.
    """
    transitions = {
        ("active", "progress"): "active",
        ("active", "complete"): "complete",
        ("active", "stale"): "stale",
        ("stale", "abandon"): "abandoned",
        ("abandoned", "replace"): "active",
    }
    return transitions.get((current, event))


def is_terminal(state):
    return state in {"abandoned", "complete"}

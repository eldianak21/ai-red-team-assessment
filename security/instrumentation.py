import json
from pathlib import Path
from datetime import datetime, timezone

LOG_FILE = Path("logs/security_events.jsonl")


def log_security_event(
    event,
    attack=None,
    true_label=None,
    original_prediction=None,
    adversarial_prediction=None,
    original_confidence=None,
    adversarial_confidence=None,
    epsilon=None,
    alpha=None,
    iterations=None,
    success=None,
    duration_ms=None,
):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "attack": attack,
        "true_label": true_label,
        "original_prediction": original_prediction,
        "adversarial_prediction": adversarial_prediction,
        "original_confidence": original_confidence,
        "adversarial_confidence": adversarial_confidence,
        "epsilon": epsilon,
        "alpha": alpha,
        "iterations": iterations,
        "success": success,
        "duration_ms": duration_ms,
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print("Security event recorded:")
    print(json.dumps(record, indent=2))

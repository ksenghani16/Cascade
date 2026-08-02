# ml_service/audit_log.py
import hashlib
import json
import time
import os

LOG_FILE = "../storage/audit_log.jsonl"

def _get_last_hash():
    if not os.path.exists(LOG_FILE):
        return "0" * 64
    with open(LOG_FILE, "rb") as f:
        lines = f.readlines()
        if not lines:
            return "0" * 64
        return json.loads(lines[-1])["entry_hash"]

def log_decision(ticket_id: str, stage: str, details: dict):
    prev_hash = _get_last_hash()
    entry = {
        "timestamp": time.time(),
        "ticket_id": ticket_id,
        "stage": stage,
        "details": details,
        "prev_hash": prev_hash,
    }
    entry_string = json.dumps(entry, sort_keys=True)
    entry_hash = hashlib.sha256(entry_string.encode()).hexdigest()
    entry["entry_hash"] = entry_hash

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry_hash

def verify_log_integrity():
    if not os.path.exists(LOG_FILE):
        return True, None
    with open(LOG_FILE) as f:
        lines = [json.loads(l) for l in f.readlines()]

    prev_hash = "0" * 64
    for i, entry in enumerate(lines):
        stored_hash = entry["entry_hash"]
        recomputed = dict(entry)
        del recomputed["entry_hash"]
        recomputed_hash = hashlib.sha256(json.dumps(recomputed, sort_keys=True).encode()).hexdigest()
        if recomputed_hash != stored_hash or entry["prev_hash"] != prev_hash:
            return False, i
        prev_hash = stored_hash
    return True, None
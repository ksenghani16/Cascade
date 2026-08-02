# ml_service/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
import json
import os
import time

from embeddings import embed_text
from clustering import check_novelty
from anomaly import check_anomaly
from threshold_bandit import choose_threshold, record_threshold_outcome
from bandit import choose_strategy, record_outcome
from audit_log import log_decision

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

classifier = joblib.load("../storage/classifier.joblib")

AUTO_REPLY_TEMPLATES = {
    "billing": "Thanks for reaching out. We've identified this as a billing issue and are reviewing your account now. If this involves a duplicate charge, a refund will be processed automatically within 3-5 business days.",
    "technical": "Thanks for reporting this. Our system has flagged this as a known technical issue and our team is already working on it. We'll follow up if any action is needed on your end.",
    "account": "We've received your account-related request and are processing it now. You'll receive a confirmation email once the change has been applied.",
    "general": "Thanks for your message! We've noted your request and someone from our team will follow up if further action is needed.",
}

REVIEW_QUEUE_FILE = "../storage/review_queue.json"

def load_queue():
    if not os.path.exists(REVIEW_QUEUE_FILE):
        return []
    with open(REVIEW_QUEUE_FILE) as f:
        return json.load(f)

def save_queue(queue):
    with open(REVIEW_QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)


class Ticket(BaseModel):
    ticket_id: str
    text: str
    account_age_days: int
    prior_tickets_30d: int

@app.post("/triage")
def triage(ticket: Ticket):
    text_embedding = np.array(embed_text(ticket.text))
    numeric = np.array([ticket.account_age_days, ticket.prior_tickets_30d])
    X = [np.concatenate([text_embedding, numeric])]

    # STAGE 1: classify + calibrated confidence
    pred_class = classifier.predict(X)[0]
    pred_proba = max(classifier.predict_proba(X)[0])

    threshold = choose_threshold(pred_class)

    log_decision(ticket.ticket_id, "stage1_classifier",
                 {"prediction": pred_class, "confidence": pred_proba, "threshold_used": threshold})

    if pred_proba >= threshold:
        reply_text = AUTO_REPLY_TEMPLATES.get(pred_class, "Thanks for your message — we're looking into this now.")
        log_decision(ticket.ticket_id, "auto_resolved",
                      {"category": pred_class, "threshold_used": threshold, "reply": reply_text})
        return {"ticket_id": ticket.ticket_id, "action": "auto_reply",
                "category": pred_class, "confidence": pred_proba,
                "threshold_used": threshold, "llm_used": False,
                "reply_text": reply_text}

    # STAGE 2: novelty + anomaly checks
    is_novel, novelty_score = check_novelty(ticket.text)
    is_anomaly, anomaly_score = check_anomaly(ticket.account_age_days, ticket.prior_tickets_30d)
    log_decision(ticket.ticket_id, "stage2_clustering_anomaly",
                 {"is_novel": is_novel, "novelty_score": novelty_score,
                  "is_anomaly": is_anomaly, "anomaly_score": anomaly_score})

    if is_novel or is_anomaly:
        reason = "novel" if is_novel else "anomalous"
        log_decision(ticket.ticket_id, "flagged_for_human", {"reason": reason})

        queue = load_queue()
        queue.append({
            "ticket_id": ticket.ticket_id,
            "text": ticket.text,
            "account_age_days": ticket.account_age_days,
            "prior_tickets_30d": ticket.prior_tickets_30d,
            "predicted_category": pred_class,
            "predicted_confidence": pred_proba,
            "reason": reason,
            "status": "pending",
            "timestamp": time.time()
        })
        save_queue(queue)

        return {"ticket_id": ticket.ticket_id, "action": "route_to_human",
                "reason": "novel_or_anomalous", "llm_used": False}

    # STAGE 3 happens in n8n — signal that this ticket needs the LLM agent
    log_decision(ticket.ticket_id, "routed_to_llm_agent", {})

    # STAGE 4: bandit picks the response strategy
    strategy = choose_strategy()
    log_decision(ticket.ticket_id, "stage4_bandit", {"strategy_chosen": strategy})

    return {"ticket_id": ticket.ticket_id, "action": "needs_llm_agent",
            "response_strategy": strategy, "threshold_used": threshold,
            "category": pred_class, "llm_used": True}


class Outcome(BaseModel):
    ticket_id: str
    category: str
    threshold_used: float
    strategy: str = None
    ticket_was_reopened: bool
    time_to_resolution_minutes: float = 0.0
    cost_incurred: float = 0.0

@app.post("/feedback")
def feedback(outcome: Outcome):
    record_threshold_outcome(outcome.category, outcome.threshold_used, outcome.ticket_was_reopened)
    if outcome.strategy:
        record_outcome(outcome.strategy, not outcome.ticket_was_reopened,
                        outcome.time_to_resolution_minutes, outcome.cost_incurred)
    log_decision(outcome.ticket_id, "human_feedback", outcome.dict())
    return {"status": "recorded"}


@app.get("/review-queue")
def get_review_queue():
    queue = load_queue()
    return [item for item in queue if item["status"] == "pending"]

class ReviewResolution(BaseModel):
    ticket_id: str
    correct_category: str
    notes: str = ""

@app.post("/review-queue/resolve")
def resolve_review(resolution: ReviewResolution):
    queue = load_queue()
    for item in queue:
        if item["ticket_id"] == resolution.ticket_id and item["status"] == "pending":
            item["status"] = "resolved"
            item["correct_category"] = resolution.correct_category
            item["notes"] = resolution.notes
            log_decision(resolution.ticket_id, "human_review_resolved", {
                "correct_category": resolution.correct_category,
                "notes": resolution.notes
            })
            save_queue(queue)
            return {"status": "resolved", "ticket_id": resolution.ticket_id}
    return {"status": "not_found"}
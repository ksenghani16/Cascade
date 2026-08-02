# training/generate_synthetic_tickets.py
import pandas as pd
import numpy as np
import random

random.seed(42)
np.random.seed(42)

CATEGORY_TEMPLATES = {
    "billing": [
        "I was charged twice for my subscription this month.",
        "My invoice shows the wrong amount, can you fix it?",
        "I want a refund for a purchase I didn't make.",
        "Why did my card get billed before the trial ended?",
    ],
    "technical": [
        "The app crashes every time I try to upload a file.",
        "I can't log in, it just spins and never loads.",
        "The export feature is producing corrupted files.",
        "Your API is returning a 500 error on every request.",
    ],
    "account": [
        "I forgot my password and the reset link isn't working.",
        "Can you change the email address on my account?",
        "I need to delete my account and all my data.",
        "My account got locked after too many login attempts.",
    ],
    "general": [
        "Do you have a mobile app for this?",
        "What are your business hours?",
        "I just wanted to say your support team was great.",
        "Is there a student discount available?",
    ],
}

def generate_tickets(n_per_category=150):
    rows = []
    for category, templates in CATEGORY_TEMPLATES.items():
        for _ in range(n_per_category):
            base = random.choice(templates)
            # add small random variation so not every ticket is identical text
            noise_words = ["please help", "urgent", "thanks", "asap", ""]
            text = f"{base} {random.choice(noise_words)}".strip()
            account_age_days = np.random.randint(1, 2000)
            prior_tickets_30d = np.random.poisson(1.2)
            rows.append([text, category, account_age_days, prior_tickets_30d])

    return pd.DataFrame(rows, columns=["text", "category", "account_age_days", "prior_tickets_30d"])

df = generate_tickets()
df.to_csv("ml_service/data/tickets.csv", index=False)
print(df["category"].value_counts())
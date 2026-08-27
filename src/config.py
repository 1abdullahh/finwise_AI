"""
config.py
Loads environment settings and holds static form options used across the app.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# API / Model settings
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

# ---------------------------------------------------------------------------
# Cache settings
# ---------------------------------------------------------------------------
SQLITE_CACHE_PATH = os.getenv("SQLITE_CACHE_PATH", ".cache/finwise_cache.db")

# ---------------------------------------------------------------------------
# Form options
# ---------------------------------------------------------------------------
FINANCIAL_GOALS = [
    "Save money",
    "Build an emergency fund",
    "Pay off debt",
    "Plan a vacation",
    "Start a business",
    "Improve budgeting",
]

CURRENCIES = ["USD", "PKR", "EUR", "GBP", "INR", "AED", "CAD", "AUD"]

EXPENSE_CATEGORIES = [
    "housing_rent",
    "food",
    "transportation",
    "utilities",
    "education",
    "healthcare",
    "entertainment",
    "loan_debt",
    "other",
]

EXPENSE_LABELS = {
    "housing_rent": "Housing / Rent",
    "food": "Food",
    "transportation": "Transportation",
    "utilities": "Utilities",
    "education": "Education",
    "healthcare": "Healthcare",
    "entertainment": "Entertainment",
    "loan_debt": "Loan / Debt",
    "other": "Other",
}

# ---------------------------------------------------------------------------
# Educational disclaimer (shown on every relevant screen)
# ---------------------------------------------------------------------------
DISCLAIMER = (
    "⚠️ **Educational Prototype Only.** FinWise AI does not provide guaranteed "
    "investment advice, does not execute financial transactions, and is not "
    "connected to any real bank account. Nothing shown here is a guaranteed "
    "financial outcome. Please consult a qualified financial professional "
    "before making real financial decisions."
)

APP_TITLE = "💰 FinWise AI"
APP_SUBTITLE = "AI-Powered Personal Financial Analysis & Smart Budget Assistant"

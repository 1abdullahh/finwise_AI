"""
utils.py
Safe JSON parsing and small shared helpers.
"""

import json
import re
from typing import Any, Dict, Optional

REQUIRED_KEYS = [
    "financial_summary",
    "financial_health_score",
    "spending_analysis",
    "risk_level",
    "top_priorities",
    "budget_recommendations",
    "savings_strategy",
    "next_month_action_plan",
]

FALLBACK_RESPONSE: Dict[str, Any] = {
    "financial_summary": (
        "We couldn't generate a full AI analysis this time, but your "
        "Python-calculated numbers below are accurate and safe to use."
    ),
    "financial_health_score": 0,
    "spending_analysis": [],
    "risk_level": "UNKNOWN",
    "top_priorities": ["Try running the analysis again."],
    "budget_recommendations": [],
    "savings_strategy": [],
    "next_month_action_plan": [],
}


def extract_json_block(text: str) -> Optional[str]:
    """Pull the first {...} JSON object out of a raw LLM string, stripping
    markdown code fences if present."""
    if not text:
        return None

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())
    cleaned = cleaned.strip()

    # Find the outermost JSON object using brace matching.
    start = cleaned.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(cleaned)):
        if cleaned[i] == "{":
            depth += 1
        elif cleaned[i] == "}":
            depth -= 1
            if depth == 0:
                return cleaned[start : i + 1]
    return None


def safe_parse_json(raw_text: str) -> Dict[str, Any]:
    """
    Attempt to parse the LLM's raw output into the expected schema.
    Falls back to FALLBACK_RESPONSE (with an error note) on any failure,
    so the Streamlit app never crashes on a malformed response.
    """
    block = extract_json_block(raw_text)
    if block is None:
        result = dict(FALLBACK_RESPONSE)
        result["financial_summary"] = (
            "The AI response could not be parsed as JSON. Raw output has been "
            "logged for debugging. Your calculated numbers are still shown below."
        )
        return result

    try:
        data = json.loads(block)
    except json.JSONDecodeError:
        result = dict(FALLBACK_RESPONSE)
        result["financial_summary"] = (
            "The AI response was not valid JSON and could not be parsed. "
            "Your calculated numbers are still shown below."
        )
        return result

    # Fill any missing keys with safe defaults instead of crashing the UI.
    for key in REQUIRED_KEYS:
        if key not in data:
            data[key] = FALLBACK_RESPONSE[key]

    # Type safety nets
    try:
        data["financial_health_score"] = int(data["financial_health_score"])
    except (TypeError, ValueError):
        data["financial_health_score"] = 0

    if data.get("risk_level") not in ("LOW", "MEDIUM", "HIGH"):
        data["risk_level"] = str(data.get("risk_level", "UNKNOWN")).upper() or "UNKNOWN"

    if not isinstance(data.get("spending_analysis"), list):
        data["spending_analysis"] = []

    for list_key in ("top_priorities", "budget_recommendations", "savings_strategy", "next_month_action_plan"):
        if not isinstance(data.get(list_key), list):
            data[list_key] = []

    return data


def score_band(score: int) -> str:
    """Educational-only score band label."""
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Generally healthy"
    if score >= 40:
        return "Needs improvement"
    return "High attention"


def format_currency(value: float, currency: str = "USD") -> str:
    symbols = {"USD": "$", "PKR": "Rs ", "EUR": "€", "GBP": "£", "INR": "₹"}
    symbol = symbols.get(currency, f"{currency} ")
    return f"{symbol}{value:,.2f}"

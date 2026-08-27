"""
prompts.py

All prompt engineering lives here:
- SYSTEM_PROMPT (role + safety rules for SystemMessage)
- JSON_SCHEMA_DESCRIPTION (exact schema the model must return)
- FINANCIAL_PROMPT_TEMPLATE (PromptTemplate, single reusable string)
- FINANCIAL_CHAT_TEMPLATE (ChatPromptTemplate: system + human, JSON output)
- NARRATIVE_CHAT_TEMPLATE (ChatPromptTemplate used for the streamed
  free-text recommendation shown live in the UI)
"""

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

# ---------------------------------------------------------------------------
# System role + safety rules
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are FinWise AI, an educational personal-finance assistant.

Your role:
- Analyse the user's monthly income, expenses, and savings that Python has
  already calculated for you.
- Produce clear, structured, and encouraging budgeting insights.
- Identify high-expense areas, risk patterns, and realistic improvement steps.

Safety rules (must always follow):
1. You are NOT a licensed financial advisor. Never claim to be one.
2. Never guarantee any financial outcome (returns, savings growth, debt
   payoff timelines, investment performance, etc).
3. Never recommend specific investment products, stocks, cryptocurrencies,
   or brokers.
4. Never claim to execute, schedule, or connect to any real transaction or
   bank account. You only analyse the numbers you are given.
5. Always frame your response as general education, and remind the user to
   consult a qualified financial professional for real decisions.
6. Base every observation strictly on the numbers provided — do not invent
   income, expenses, or account balances that were not given to you.
7. Keep tone supportive and non-judgmental, even when risk is high.
"""

JSON_SCHEMA_DESCRIPTION = """Return ONLY a single valid JSON object with EXACTLY this schema
and no extra commentary, no markdown code fences, and no text before or after it:

{{
  "financial_summary": "string - 2-3 sentence plain-language summary",
  "financial_health_score": 0,
  "spending_analysis": [
    {{"category": "string", "observation": "string", "recommendation": "string"}}
  ],
  "risk_level": "LOW | MEDIUM | HIGH",
  "top_priorities": ["string", "string"],
  "budget_recommendations": ["string", "string"],
  "savings_strategy": ["string", "string"],
  "next_month_action_plan": ["string", "string"]
}}

Scoring bands (educational only, must stay consistent with financial_health_score):
- 80-100: strong
- 60-79: generally healthy
- 40-59: needs improvement
- below 40: high attention
"""

# ---------------------------------------------------------------------------
# PromptTemplate: single reusable string template with financial variables
# ---------------------------------------------------------------------------
FINANCIAL_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "monthly_income",
        "total_expenses",
        "remaining_income",
        "savings",
        "savings_ratio",
        "expense_ratio",
        "financial_goal",
        "expense_breakdown",
    ],
    template="""Analyse this user's monthly financial snapshot.

Monthly income: {monthly_income}
Total expenses: {total_expenses}
Remaining income: {remaining_income}
Current savings: {savings}
Savings ratio: {savings_ratio}%
Expense ratio: {expense_ratio}%
Financial goal: {financial_goal}

Expense breakdown:
{expense_breakdown}

Provide a personalized, structured budgeting analysis based only on these numbers.
""",
)

# ---------------------------------------------------------------------------
# ChatPromptTemplate: System + Human, carries safety rules + JSON schema + data
# ---------------------------------------------------------------------------
FINANCIAL_CHAT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT + "\n" + JSON_SCHEMA_DESCRIPTION),
        (
            "human",
            """Here is my financial snapshot for this month:

Monthly income: {monthly_income}
Total expenses: {total_expenses}
Remaining income: {remaining_income}
Current savings: {savings}
Savings ratio: {savings_ratio}%
Expense ratio: {expense_ratio}%
Financial goal: {financial_goal}

Expense breakdown:
{expense_breakdown}

Please analyse this and respond with the JSON object described in your instructions.""",
        ),
    ]
)

# ---------------------------------------------------------------------------
# ChatPromptTemplate for the streamed, free-text narrative recommendation
# (shown live in the UI via .stream() / st.write_stream())
# ---------------------------------------------------------------------------
NARRATIVE_CHAT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            """Based on this financial snapshot, write a short, warm, plain-language
paragraph (4-6 sentences) of educational budgeting recommendations. Do not
use JSON here — natural written prose only.

Monthly income: {monthly_income}
Total expenses: {total_expenses}
Remaining income: {remaining_income}
Current savings: {savings}
Savings ratio: {savings_ratio}%
Expense ratio: {expense_ratio}%
Financial goal: {financial_goal}

Expense breakdown:
{expense_breakdown}""",
        ),
    ]
)

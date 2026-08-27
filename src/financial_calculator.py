"""
financial_calculator.py

ALL deterministic math lives here. Same inputs -> same outputs, always.
No LLM calls happen in this file. This is intentionally kept separate from
the AI layer so the two responsibilities never mix (see README for the
Python-vs-AI explanation).
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class FinancialCalculation:
    monthly_income: float
    expenses: Dict[str, float]
    savings: float
    total_expenses: float = field(init=False)
    remaining_income: float = field(init=False)
    savings_ratio: float = field(init=False)
    expense_ratio: float = field(init=False)
    debt_ratio: float = field(init=False)
    preliminary_score: int = field(init=False)

    def __post_init__(self):
        self.total_expenses = calculate_total_expenses(self.expenses)
        self.remaining_income = calculate_remaining_income(
            self.monthly_income, self.total_expenses
        )
        self.savings_ratio = calculate_savings_ratio(self.savings, self.monthly_income)
        self.expense_ratio = calculate_expense_ratio(
            self.total_expenses, self.monthly_income
        )
        self.debt_ratio = calculate_debt_ratio(
            self.expenses.get("loan_debt", 0), self.monthly_income
        )
        self.preliminary_score = calculate_preliminary_score(
            savings_ratio=self.savings_ratio,
            remaining_income=self.remaining_income,
            expense_ratio=self.expense_ratio,
            debt_ratio=self.debt_ratio,
        )

    def as_dict(self) -> dict:
        return {
            "monthly_income": self.monthly_income,
            "expenses": self.expenses,
            "total_expenses": self.total_expenses,
            "remaining_income": self.remaining_income,
            "savings": self.savings,
            "savings_ratio": self.savings_ratio,
            "expense_ratio": self.expense_ratio,
            "debt_ratio": self.debt_ratio,
            "preliminary_score": self.preliminary_score,
        }


def calculate_total_expenses(expenses: Dict[str, float]) -> float:
    """Sum of every expense category."""
    return round(sum(float(v) for v in expenses.values()), 2)


def calculate_remaining_income(monthly_income: float, total_expenses: float) -> float:
    """Income left over after all expenses."""
    return round(monthly_income - total_expenses, 2)


def calculate_savings_ratio(savings: float, monthly_income: float) -> float:
    """(savings / income) * 100, guarded against divide-by-zero."""
    if monthly_income <= 0:
        return 0.0
    return round((savings / monthly_income) * 100, 2)


def calculate_expense_ratio(total_expenses: float, monthly_income: float) -> float:
    """(total_expenses / income) * 100, guarded against divide-by-zero."""
    if monthly_income <= 0:
        return 0.0
    return round((total_expenses / monthly_income) * 100, 2)


def calculate_debt_ratio(loan_debt: float, monthly_income: float) -> float:
    """(loan/debt expense / income) * 100, guarded against divide-by-zero."""
    if monthly_income <= 0:
        return 0.0
    return round((loan_debt / monthly_income) * 100, 2)


def calculate_preliminary_score(
    savings_ratio: float,
    remaining_income: float,
    expense_ratio: float,
    debt_ratio: float,
) -> int:
    """
    Weighted 0-100 heuristic used as a deterministic starting point before
    the LLM adds qualitative insight. Pure Python, no AI.

    Weights:
      - Savings ratio        : 35%
      - Leftover income sign : 25%
      - Expense ratio        : 25%
      - Debt burden          : 15%
    """
    # Savings component: 30% savings ratio -> full marks
    savings_component = min(savings_ratio / 30 * 35, 35)

    # Leftover component: negative remaining income is heavily penalized
    if remaining_income < 0:
        leftover_component = 0
    else:
        leftover_component = 25

    # Expense ratio component: lower is better. 100%+ expense ratio -> 0.
    expense_component = max(0, 25 - (expense_ratio - 50) / 2) if expense_ratio > 50 else 25

    # Debt component: lower debt ratio is better. 40%+ debt ratio -> 0.
    debt_component = max(0, 15 - (debt_ratio / 40) * 15)

    score = savings_component + leftover_component + expense_component + debt_component
    return int(round(max(0, min(score, 100))))


def build_expense_breakdown_text(expenses: Dict[str, float], labels: Dict[str, str]) -> str:
    """Human-readable expense breakdown string for prompt injection."""
    lines = [
        f"- {labels.get(key, key)}: {value:,.2f}"
        for key, value in expenses.items()
        if value > 0
    ]
    return "\n".join(lines) if lines else "No expenses reported."

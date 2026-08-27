"""
app.py — FinWise AI
Run with: streamlit run app.py

Streamlit UI only. All financial math lives in src/financial_calculator.py.
All LangChain wiring lives in src/chains.py, src/prompts.py, src/cache_manager.py.
"""

import json
import time

import streamlit as st

from src import config
from src.financial_calculator import (
    FinancialCalculation,
    build_expense_breakdown_text,
)
from src.chains import (
    build_llm,
    build_financial_analysis_chain,
    run_financial_analysis,
    demo_message_roles,
    stream_recommendations,
)
from src.cache_manager import configure_cache, CACHE_DESCRIPTIONS
from src.utils import safe_parse_json, score_band, format_currency

st.set_page_config(page_title=config.APP_TITLE, page_icon="💰", layout="wide")

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "calc_result" not in st.session_state:
    st.session_state.calc_result = None
if "narrative_done" not in st.session_state:
    st.session_state.narrative_done = ""
if "openai_api_key" not in st.session_state:
    # Pre-fill from .env only if present; user can still override/clear it
    # from the sidebar field below.
    st.session_state.openai_api_key = config.OPENAI_API_KEY or ""

with st.sidebar:
    st.title(config.APP_TITLE)
    st.caption(config.APP_SUBTITLE)
    st.info(config.DISCLAIMER)

    st.divider()
    st.subheader("🔑 OpenAI API Key")
    api_key_input = st.text_input(
        "Enter your OpenAI API key",
        value=st.session_state.openai_api_key,
        type="password",
        placeholder="sk-...",
        help="Your key is kept only in this browser session and is never saved to disk.",
    )
    st.session_state.openai_api_key = api_key_input.strip()

    if st.session_state.openai_api_key:
        st.caption("✅ Key set — AI features are enabled.")
    else:
        st.caption("⚠️ Enter a key above to enable AI features.")

    st.divider()
    st.subheader("⚙️ Model Settings")
    model_name = st.text_input("Model", value=config.DEFAULT_MODEL)
    temperature = st.slider("Temperature", 0.0, 1.0, config.DEFAULT_TEMPERATURE, 0.05)

    st.subheader("🗄️ Cache Settings")
    cache_choice = st.radio(
        "Cache backend",
        options=["in_memory", "sqlite", "none"],
        format_func=lambda x: {"in_memory": "In-Memory", "sqlite": "SQLite (persistent)", "none": "Disabled"}[x],
        index=0,
    )
    active_cache = configure_cache(cache_choice)
    st.caption(CACHE_DESCRIPTIONS[active_cache])

    st.divider()
    if st.button("🔄 Reset Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.divider()
    st.caption("Course Module: Building LLM Applications with LangChain")
    st.caption("Educational prototype — not a real financial product.")


st.title(config.APP_TITLE)
st.caption(config.APP_SUBTITLE)
st.warning(config.DISCLAIMER)

tab_form, tab_dashboard, tab_about = st.tabs(["📝 Enter Your Finances", "📊 AI Dashboard", "ℹ️ About"])

with tab_form:
    with st.form("financial_form"):
        col1, col2 = st.columns(2)

        with col1:
            monthly_income = st.number_input(
                "Monthly income", min_value=0.0, value=5000.0, step=100.0
            )
            savings = st.number_input(
                "Current monthly savings", min_value=0.0, value=500.0, step=50.0
            )
            currency = st.selectbox("Currency", config.CURRENCIES, index=0)

        with col2:
            financial_goal = st.selectbox("Financial goal", config.FINANCIAL_GOALS)

        st.markdown("#### Monthly Expenses")
        expense_cols = st.columns(3)
        expenses = {}
        for i, cat in enumerate(config.EXPENSE_CATEGORIES):
            with expense_cols[i % 3]:
                expenses[cat] = st.number_input(
                    config.EXPENSE_LABELS[cat],
                    min_value=0.0,
                    value=0.0,
                    step=50.0,
                    key=f"exp_{cat}",
                )

        with st.expander("🔍 Preview expense breakdown"):
            st.json(expenses)

        submitted = st.form_submit_button("🚀 Analyze My Finances", use_container_width=True)

    if submitted:
        calc = FinancialCalculation(
            monthly_income=monthly_income, expenses=expenses, savings=savings
        )
        st.session_state.calc_result = calc
        st.session_state.currency = currency
        st.session_state.financial_goal = financial_goal
        st.session_state.analysis_result = None  # force re-run of AI tab
        st.success("Calculations complete! Head to the **AI Dashboard** tab to view your analysis.")


with tab_dashboard:
    calc = st.session_state.get("calc_result")

    if calc is None:
        st.info("Fill in the form under **Enter Your Finances** and submit to see your dashboard.")
    else:
        currency = st.session_state.get("currency", "USD")
        financial_goal = st.session_state.get("financial_goal", config.FINANCIAL_GOALS[0])

        st.subheader("📌 Financial Overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Monthly Income", format_currency(calc.monthly_income, currency))
        m2.metric("Total Expenses", format_currency(calc.total_expenses, currency))
        m3.metric(
            "Remaining Income",
            format_currency(calc.remaining_income, currency),
            delta=f"{calc.expense_ratio:.1f}% of income spent",
        )
        m4.metric("Current Savings", format_currency(calc.savings, currency))

        st.progress(
            min(max(calc.preliminary_score, 0), 100) / 100,
            text=f"Preliminary score (Python heuristic): {calc.preliminary_score}/100",
        )

        st.divider()
        st.subheader("🤖 AI-Generated Analysis")

        expense_breakdown_text = build_expense_breakdown_text(
            calc.expenses, config.EXPENSE_LABELS
        )
        chain_inputs = {
            "monthly_income": calc.monthly_income,
            "total_expenses": calc.total_expenses,
            "remaining_income": calc.remaining_income,
            "savings": calc.savings,
            "savings_ratio": calc.savings_ratio,
            "expense_ratio": calc.expense_ratio,
            "financial_goal": financial_goal,
            "expense_breakdown": expense_breakdown_text,
        }

        run_col, _ = st.columns([1, 3])
        run_analysis = run_col.button("✨ Generate AI Insights", use_container_width=True)

        if run_analysis:
            api_key = st.session_state.get("openai_api_key", "")
            if not api_key:
                st.error(
                    "No API key set. Enter your OpenAI API key in the sidebar to continue."
                )
            else:
                # Structured JSON analysis via the reusable LLMChain
                with st.spinner("Analyzing your financial data..."):
                    try:
                        llm = build_llm(streaming=False, temperature=temperature, api_key=api_key)
                        chain = build_financial_analysis_chain(llm)
                        raw_text = run_financial_analysis(chain, chain_inputs)
                        parsed = safe_parse_json(raw_text)
                        st.session_state.analysis_result = parsed
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"AI analysis failed: {exc}")
                        st.session_state.analysis_result = None

                # --- Streamed narrative recommendation ---
                st.markdown("##### 📝 Live Recommendation")
                placeholder_llm = build_llm(streaming=True, temperature=temperature, api_key=api_key)
                try:
                    full_text = st.write_stream(
                        stream_recommendations(placeholder_llm, chain_inputs)
                    )
                    st.session_state.narrative_done = full_text
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Streaming failed: {exc}")

        result = st.session_state.get("analysis_result")

        if result:
            st.divider()
            score = result.get("financial_health_score", 0)
            risk = result.get("risk_level", "UNKNOWN")

            sc1, sc2 = st.columns([2, 1])
            with sc1:
                st.progress(
                    min(max(score, 0), 100) / 100,
                    text=f"AI Financial Health Score: {score}/100 — {score_band(score)}",
                )
            with sc2:
                risk_colors = {"LOW": "success", "MEDIUM": "warning", "HIGH": "error"}
                box = getattr(st, risk_colors.get(risk, "info"))
                box(f"Risk level: **{risk}**")

            st.markdown("##### Summary")
            st.write(result.get("financial_summary", ""))

            with st.expander("📊 Spending Analysis", expanded=True):
                for item in result.get("spending_analysis", []):
                    st.markdown(
                        f"**{item.get('category', 'Category')}** — {item.get('observation', '')}\n\n"
                        f"💡 *{item.get('recommendation', '')}*"
                    )
                    st.divider()

            tp, br, ss, ap = st.tabs(
                ["🎯 Priorities", "💵 Budget Tips", "🏦 Savings Strategy", "📅 Next Month Plan"]
            )
            with tp:
                for p in result.get("top_priorities", []):
                    st.markdown(f"- {p}")
            with br:
                for b in result.get("budget_recommendations", []):
                    st.markdown(f"- {b}")
            with ss:
                for s in result.get("savings_strategy", []):
                    st.markdown(f"- {s}")
            with ap:
                for a in result.get("next_month_action_plan", []):
                    st.markdown(f"- {a}")

            st.caption(config.DISCLAIMER)

        with st.expander("🛠️ Developer: Raw message roles demo (SystemMessage / HumanMessage / AIMessage)"):
            messages = demo_message_roles(chain_inputs)
            for msg in messages:
                st.code(f"{msg.__class__.__name__}: {msg.content}", language="text")

with tab_about:
    st.subheader("About FinWise AI")
    st.write(
        """
FinWise AI is an educational LangChain + Streamlit prototype built for the
**Building LLM Applications with LangChain** course module. It demonstrates:

- Deterministic Python financial calculations, fully separated from AI logic.
- `ChatOpenAI` integration with `PromptTemplate` and `ChatPromptTemplate`.
- A reusable `LLMChain` returning structured JSON, safely parsed.
- Live streaming of AI recommendations with `.stream()` and `st.write_stream()`.
- Switchable `InMemoryCache` / `SQLiteCache` for LangChain LLM calls.
"""
    )
    st.warning(config.DISCLAIMER)
    st.caption("Total marks: 100 · Submission: GitHub repository + demo")

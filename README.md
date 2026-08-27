# FinWise AI

**AI-Powered Personal Financial Analysis and Smart Budget Assistant**
A LangChain + Streamlit FinTech prototype built for the *Building LLM Applications with LangChain* course module.

> ⚠️ **Educational prototype only.** FinWise AI does not provide guaranteed investment advice, does not execute financial transactions, and is not connected to any real bank account. Consult a qualified financial professional before making real financial decisions.

---

## 1. Project Structure

```
finwise_ai/
├── app.py                     # Streamlit UI — run this
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── src/
│   ├── __init__.py
│   ├── config.py              # settings + form options
│   ├── prompts.py              # PromptTemplate + ChatPromptTemplate + JSON schema
│   ├── financial_calculator.py # deterministic maths — no AI
│   ├── chains.py               # ChatOpenAI, LLMChain, streaming
│   ├── cache_manager.py        # in-memory + SQLite caching
│   └── utils.py                # safe JSON parsing + helpers
└── docs/
    └── FinTech_AI_Assignment.pdf
```

## 2. Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...
```

## 3. Run

```bash
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`).

## 4. How to Use

1. Go to **📝 Enter Your Finances** — fill in income, the nine expense categories, current savings, financial goal, and currency, then submit.
2. Go to **📊 AI Dashboard** — review the Python-calculated overview metrics, then click **✨ Generate AI Insights** to get:
   - A structured JSON analysis (health score, risk level, priorities, budget tips, savings strategy, next-month plan).
   - A live-streamed plain-language recommendation.
3. Use the sidebar to switch cache backend, adjust model/temperature, or reset the session.

## 5. Python vs. AI — What's Deterministic vs. What's Generative

This project **deliberately separates** two layers:

| Layer | File(s) | Behaviour |
|---|---|---|
| **Deterministic (Python)** | `src/financial_calculator.py` | Pure arithmetic: `total_expenses`, `remaining_income`, `savings_ratio`, `expense_ratio`, `debt_ratio`, and a rule-based `preliminary_score`. Same inputs **always** produce the same outputs. No API calls, no randomness. |
| **Generative (LLM)** | `src/prompts.py`, `src/chains.py` | The already-computed numbers are inserted into `PromptTemplate` / `ChatPromptTemplate`, sent to `ChatOpenAI`, and the model returns qualitative insight (summary, spending analysis, priorities, strategy) as structured JSON, plus a streamed narrative paragraph. Output can vary between runs. |

Keeping these separate means: the numbers you can verify by hand (ratios, totals) are always trustworthy math, while only the *interpretation* of those numbers comes from the AI — and it's clearly labeled as educational, not financial advice.

## 6. Caching Explained

`set_llm_cache(...)` (in `src/cache_manager.py`) registers **one global cache** for all LangChain LLM calls. Before making an API call, LangChain checks whether the exact same prompt + parameters were seen before:

| | InMemoryCache | SQLiteCache |
|---|---|---|
| Stored in | RAM | A `.db` file on disk (`.cache/finwise_cache.db`) |
| Speed | Fastest | Fast, slightly slower |
| Survives app restart? | ❌ No | ✅ Yes |
| Best for | A single session | Reusing results across sessions |

Switch between them anytime from the sidebar's **Cache Settings**. Repeating an identical request after a cache hit returns instantly and makes **no new API call**, reducing cost during testing/demoing.

## 7. Testing Scenarios

| # | Input | Expected calculation | Expected AI response |
|---|---|---|---|
| 1 | Income 8000, expenses ~2000 | Large positive remaining; high savings ratio | High score; LOW risk; growth-focused tips |
| 2 | Income 2000, expenses ~2600 | Negative remaining; expense ratio >100% | Low score; HIGH risk; urgent cost-cutting |
| 3 | Income 5000, debt 2500 | High debt share of income | MEDIUM/HIGH risk; debt-reduction priorities |
| 4 | Income 4000, savings 1200 | Savings ratio ~30% | High score; LOW risk; reinforce good habits |
| 5 | Income 3000, expenses 3000 | Remaining = 0 | MEDIUM/HIGH risk; find room to save |

## 8. Notes

- If `OPENAI_API_KEY` is missing, the app shows a clear error instead of crashing.
- All AI JSON output is parsed through `src/utils.py::safe_parse_json`, which falls back gracefully on malformed JSON so the dashboard never breaks.
- The educational disclaimer is shown on the sidebar and every relevant tab.

---
*This project is for education only. It is not financial advice and must not be used to make real investment or money decisions.*

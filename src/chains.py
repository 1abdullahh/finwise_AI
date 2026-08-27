"""
chains.py

- Builds the ChatOpenAI model.
- Builds a reusable LLMChain (financial_analysis_chain) that turns the
  PromptTemplate into structured JSON.
- Demonstrates SystemMessage / HumanMessage / AIMessage directly.
- Provides a streaming generator for the narrative recommendation.
"""

from typing import Dict, Generator

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from . import config
from .prompts import (
    SYSTEM_PROMPT,
    JSON_SCHEMA_DESCRIPTION,
    FINANCIAL_PROMPT_TEMPLATE,
    NARRATIVE_CHAT_TEMPLATE,
)

# ---------------------------------------------------------------------------
# LLMChain import with a safe fallback.
#
# Some environments end up with an incomplete/mismatched `langchain` install
# (e.g. only `langchain-core` present) where `langchain.chains` does not
# exist, raising: ModuleNotFoundError: No module named 'langchain.chains'.
#
# If that happens, we fall back to a tiny LCEL-based wrapper that behaves
# like LLMChain (same .invoke(inputs) -> {"text": ...} interface) built
# only from langchain-core, which is always installed alongside
# langchain-openai. This keeps the rest of the app unchanged either way.
# ---------------------------------------------------------------------------
try:
    from langchain.chains import LLMChain  # type: ignore

    _HAS_LEGACY_LLMCHAIN = True
except ModuleNotFoundError:
    _HAS_LEGACY_LLMCHAIN = False

    class LLMChain:  # minimal drop-in replacement using LCEL
        """
        Lightweight LLMChain-compatible wrapper built with LCEL
        (prompt | llm), used only when the real `langchain.chains.LLMChain`
        is unavailable in the installed environment.
        """

        def __init__(self, llm, prompt):
            self.llm = llm
            self.prompt = prompt
            self._runnable = prompt | llm

        def invoke(self, inputs: Dict) -> Dict:
            result = self._runnable.invoke(inputs)
            text = result.content if hasattr(result, "content") else str(result)
            return {"text": text}


def build_llm(streaming: bool = False, temperature: float = None, api_key: str = None) -> ChatOpenAI:
    """Create the ChatOpenAI model used across the app.

    api_key, if provided (e.g. entered by the user in the browser at
    runtime), takes priority over the key loaded from the .env file in
    config.py. This lets the app run purely from a key the user types in
    the UI, with no .env file required.
    """
    return ChatOpenAI(
        model=config.DEFAULT_MODEL,
        api_key=api_key or config.OPENAI_API_KEY,
        temperature=temperature if temperature is not None else config.DEFAULT_TEMPERATURE,
        streaming=streaming,
    )


def build_financial_analysis_chain(llm: ChatOpenAI = None) -> LLMChain:
    """
    Reusable LLMChain: PromptTemplate (single string) -> LLM -> raw text.
    The raw text is expected to be a JSON string (parsed later in utils.py).
    Note: the JSON schema instructions are prepended so the chain can be
    used standalone even without the ChatPromptTemplate.
    """
    llm = llm or build_llm(streaming=False)

    # Wrap the plain PromptTemplate with the system-level JSON instructions
    # so this chain alone is enough to get structured output.
    json_instructed_template = FINANCIAL_PROMPT_TEMPLATE.partial()
    full_template = FINANCIAL_PROMPT_TEMPLATE

    # Prepend schema + safety instructions to the template text once.
    full_template.template = (
        SYSTEM_PROMPT + "\n" + JSON_SCHEMA_DESCRIPTION + "\n\n" + FINANCIAL_PROMPT_TEMPLATE.template
    ) if not FINANCIAL_PROMPT_TEMPLATE.template.startswith("You are FinWise AI") else FINANCIAL_PROMPT_TEMPLATE.template

    return LLMChain(llm=llm, prompt=full_template)


def run_financial_analysis(chain: LLMChain, inputs: Dict) -> str:
    """Run the reusable LLMChain and return the raw text response."""
    result = chain.invoke(inputs)
    # LLMChain.invoke returns a dict with the output under 'text'
    return result.get("text", "") if isinstance(result, dict) else str(result)


def demo_message_roles(inputs: Dict) -> list:
    """
    Explicit demonstration of SystemMessage / HumanMessage / AIMessage,
    as required by the assignment. Returns the message list that WOULD be
    sent to the model (used for the 'raw message demo' in the UI / README).
    """
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    human_msg = HumanMessage(
        content=(
            f"Monthly income: {inputs['monthly_income']}\n"
            f"Total expenses: {inputs['total_expenses']}\n"
            f"Remaining income: {inputs['remaining_income']}\n"
            f"Savings: {inputs['savings']}\n"
            f"Financial goal: {inputs['financial_goal']}"
        )
    )
    # Example of how a prior assistant reply is represented in history.
    ai_msg = AIMessage(
        content="Understood. I'll analyse these numbers and return a structured JSON summary."
    )
    return [system_msg, human_msg, ai_msg]


def stream_recommendations(llm: ChatOpenAI, inputs: Dict) -> Generator[str, None, None]:
    """
    Streaming generator for the narrative recommendation.
    Yields text chunks as they arrive from the model so the Streamlit UI
    can display them live with st.write_stream().
    """
    messages = NARRATIVE_CHAT_TEMPLATE.format_messages(**inputs)
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content

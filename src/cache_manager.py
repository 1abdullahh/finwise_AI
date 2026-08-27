"""
cache_manager.py

Implements both cache backends required by the assignment and a single
function to switch between them at runtime.

set_llm_cache(...) registers ONE global LangChain cache. Once set, every
subsequent LLM call is checked against that cache before hitting the API:
- Same prompt + same params -> cached result returned instantly, no new
  API call, no extra cost.
- Different prompt -> cache miss, a real API call is made and the result is
  stored for next time.

InMemoryCache lives only in RAM: fastest, but wiped when the app restarts.
SQLiteCache persists to a .db file on disk: slightly slower, but survives
restarts and can be reused across sessions.
"""

import os
from langchain_community.cache import InMemoryCache, SQLiteCache
from langchain_core.globals import set_llm_cache

from . import config

CACHE_TYPES = ("in_memory", "sqlite", "none")


def configure_cache(cache_type: str = "in_memory") -> str:
    """
    Register the requested cache type as LangChain's global LLM cache.
    Returns the cache type actually applied, for display in the UI.
    """
    if cache_type not in CACHE_TYPES:
        cache_type = "in_memory"

    if cache_type == "in_memory":
        set_llm_cache(InMemoryCache())
    elif cache_type == "sqlite":
        os.makedirs(os.path.dirname(config.SQLITE_CACHE_PATH) or ".", exist_ok=True)
        set_llm_cache(SQLiteCache(database_path=config.SQLITE_CACHE_PATH))
    else:  # "none"
        set_llm_cache(None)

    return cache_type


CACHE_DESCRIPTIONS = {
    "in_memory": "⚡ In-Memory Cache — fastest, cleared when the app restarts. Best for a single session.",
    "sqlite": "💾 SQLite Cache — stored on disk at " + config.SQLITE_CACHE_PATH + ", survives restarts. Best for reuse across sessions.",
    "none": "🚫 Caching disabled — every request calls the API fresh.",
}

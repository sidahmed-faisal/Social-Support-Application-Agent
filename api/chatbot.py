"""
api/chatbot.py

RAG over a local directory using LlamaIndex:
- Loads .txt documents from a directory (default: 'reports/')
- Builds a VectorStoreIndex (using Ollama for LLM + embeddings if available)
- Creates a chat engine and returns an answer to a user question

"""

import os
from typing import List, Optional

# LlamaIndex core
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.base.base_query_engine import BaseQueryEngine

# Ollama integrations (optional but preferred for local)
try:
    from llama_index.llms.ollama import Ollama
    from llama_index.embeddings.ollama import OllamaEmbedding
    _OLLAMA_AVAILABLE = True
except Exception:
    _OLLAMA_AVAILABLE = False


# ---- Configuration ----
_DEFAULT_DIR = "reports"
_OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_LLM_MODEL = os.environ.get("OLLAMA_LLM_MODEL", "qwen2.5vl:3b")          # text-capable
_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "all-minilm")          # small, fast


# Simple in-memory cache per directory to avoid rebuilding on each request
_INDEX_CACHE: dict[str, VectorStoreIndex] = {}


def _configure_llamaindex() -> None:
    """Configure LlamaIndex Settings to use Ollama if available; otherwise default."""
    if _OLLAMA_AVAILABLE:
        Settings.llm = Ollama(model=_LLM_MODEL, base_url=_OLLAMA_BASE_URL, request_timeout=120)
        Settings.embed_model = OllamaEmbedding(model_name=_EMBED_MODEL, base_url=_OLLAMA_BASE_URL)
    # else: let LlamaIndex fall back to its defaults (may require other LLM keys)


def _load_documents_from_dir(directory: str) -> List:
    """Load only .txt documents to avoid extra parsers; your reports are written as .txt."""
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    reader = SimpleDirectoryReader(input_dir=directory, recursive=True, required_exts=[".txt"])
    docs = reader.load_data()
    if not docs:
        raise FileNotFoundError(f"No .txt documents found in: {directory}")
    return docs


def _get_or_build_index(directory: str) -> VectorStoreIndex:
    """Return a cached index for directory; build if missing."""
    directory = directory or _DEFAULT_DIR
    key = os.path.abspath(directory)
    if key in _INDEX_CACHE:
        return _INDEX_CACHE[key]

    _configure_llamaindex()
    docs = _load_documents_from_dir(directory)
    index = VectorStoreIndex.from_documents(docs)
    _INDEX_CACHE[key] = index
    return index


def rag_answer(message: str, directory: Optional[str] = None) -> str:
    """
    Build (or reuse) an index over `directory` and answer `message`.
    Returns a plain-text answer string.
    """
    if not message or not message.strip():
        return "Please provide a non-empty question."

    index = _get_or_build_index(directory or _DEFAULT_DIR)

    # A small, retrieval-grounded chat engine
    chat_engine = index.as_chat_engine(
        similarity_top_k=4,
        chat_mode="condense_question",

    )

    response = chat_engine.chat(message)
    # LlamaIndex returns a Response object; str() gives the text
    return str(response).strip()

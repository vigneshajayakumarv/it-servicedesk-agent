"""Pluggable embedding backend. Toggle with EMBEDDINGS=local|voyage (default: local).

  local   sentence-transformers all-MiniLM-L6-v2  (free, offline, 384-dim)
  voyage  Voyage AI voyage-4 via API              (needs VOYAGE_API_KEY, 1024-dim)

The rest of the app calls embed() and never cares which backend is active.
"""
from __future__ import annotations
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

BACKEND = os.getenv("EMBEDDINGS", "local").lower()
LOCAL_MODEL = "all-MiniLM-L6-v2"
VOYAGE_MODEL = os.getenv("VOYAGE_MODEL", "voyage-4")


@lru_cache(maxsize=1)
def _local_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(LOCAL_MODEL)


@lru_cache(maxsize=1)
def _voyage_client():
    import voyageai
    return voyageai.Client()  # reads VOYAGE_API_KEY from the environment


def embed(texts: list[str], input_type: str = "document") -> list[list[float]]:
    """Embed texts. input_type is 'document' or 'query' (Voyage uses it; local ignores it)."""
    if BACKEND == "voyage":
        res = _voyage_client().embed(texts, model=VOYAGE_MODEL, input_type=input_type)
        return res.embeddings
    vecs = _local_model().encode(list(texts), normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def backend_name() -> str:
    return f"voyage:{VOYAGE_MODEL}" if BACKEND == "voyage" else f"local:{LOCAL_MODEL}"

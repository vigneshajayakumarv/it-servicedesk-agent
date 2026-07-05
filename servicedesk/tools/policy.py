"""Policy/SOP retrieval (RAG) over data/policies/*.md.

check_policy(question) -> the most relevant policy snippet(s). Embeddings are pluggable
(see embeddings.py). The index is built in-memory and cached to disk, tagged with the
backend that built it, so switching EMBEDDINGS backends rebuilds cleanly instead of
comparing vectors from two different models.

Six short docs, so cosine over an in-memory matrix is plenty; swap for Chroma/pgvector
if this ever grows to thousands of chunks.
"""
from __future__ import annotations
import json, glob
from pathlib import Path
import numpy as np

from ..embeddings import embed, backend_name

_ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = _ROOT / "data" / "policies"
INDEX = _ROOT / "data" / "policy_index.json"


def _load_chunks() -> list[dict]:
    chunks = []
    for path in sorted(glob.glob(str(POLICY_DIR / "*.md"))):
        name = Path(path).stem
        text = Path(path).read_text()
        for para in (p.strip() for p in text.split("\n\n")):
            if para and not para.startswith("#"):   # skip the title-only heading block
                chunks.append({"source": name, "text": para})
    return chunks


def build_index() -> int:
    chunks = _load_chunks()
    vectors = embed([c["text"] for c in chunks], input_type="document")
    INDEX.write_text(json.dumps(
        {"backend": backend_name(), "chunks": chunks, "vectors": vectors}))
    return len(chunks)


def _get_index() -> dict:
    if not INDEX.exists():
        build_index()
    data = json.loads(INDEX.read_text())
    if data.get("backend") != backend_name():   # backend changed -> rebuild
        build_index()
        data = json.loads(INDEX.read_text())
    return data


def check_policy(question: str, k: int = 1) -> str:
    """Return the top-k most relevant policy snippet(s) for the question."""
    data = _get_index()
    qv = np.array(embed([question], input_type="query")[0])
    mat = np.array(data["vectors"])
    sims = (mat @ qv) / (np.linalg.norm(mat, axis=1) * np.linalg.norm(qv) + 1e-9)
    top = np.argsort(-sims)[:k]
    return "\n\n".join(f"[{data['chunks'][i]['source']}] {data['chunks'][i]['text']}"
                       for i in top)

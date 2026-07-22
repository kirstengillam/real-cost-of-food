"""
RAG Q&A Lambda handler.

Receives: POST { "question": "..." }
Returns:  { "answer": "...", "sources": [...food names...] }

On cold start, downloads rag/embeddings.json from S3 into /tmp and keeps it
in memory for warm invocations. No Chroma or compiled vector DB needed.

LangSmith tracing is enabled when LANGSMITH_API_KEY and LANGSMITH_TRACING=true
are set. Each question produces a trace with three named spans:
  embed_question → retrieve_chunks → generate_answer
"""

import json
import math
import os
import pathlib
import tempfile

import anthropic
import boto3
import voyageai
from langsmith import traceable

EMBED_MODEL = "voyage-4"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
TOP_K = 4
EMBEDDINGS_S3_KEY = "rag/embeddings.json"

SYSTEM_PROMPT = (
    "You are a helpful assistant for Real Cost of Food, a site that tracks grocery "
    "prices, nutrition, and sustainability data sourced from BLS and USDA.\n\n"
    "Answer the user's question using ONLY the food data provided below. "
    "Be specific — cite actual numbers from the data when relevant. "
    "If the data doesn't cover what they're asking, say so explicitly rather than guessing. "
    "Never make up prices, nutrition figures, or sustainability ratings."
)

# Module-level cache — persists across warm invocations
_chunks: list[dict] | None = None


def _load_chunks() -> list[dict]:
    global _chunks
    if _chunks is not None:
        return _chunks

    bucket = os.environ["DATA_BUCKET"]
    s3 = boto3.client("s3")
    tmp = pathlib.Path(tempfile.gettempdir()) / "embeddings.json"
    s3.download_file(bucket, EMBEDDINGS_S3_KEY, str(tmp))
    with open(tmp) as f:
        _chunks = json.load(f)["chunks"]
    print(f"Loaded {len(_chunks)} chunks from s3://{bucket}/{EMBEDDINGS_S3_KEY}")
    return _chunks


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


@traceable(name="embed_question", run_type="embedding")
def _embed(question: str) -> list[float]:
    vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    return vo.embed([question], model=EMBED_MODEL, input_type="query").embeddings[0]


@traceable(name="retrieve_chunks", run_type="retriever")
def _retrieve(query_emb: list[float]) -> list[dict]:
    chunks = _load_chunks()
    scored = sorted(chunks, key=lambda c: _cosine(query_emb, c["embedding"]), reverse=True)
    top = scored[:TOP_K]
    # Return in a shape LangSmith understands as retrieved documents
    return [
        {
            "page_content": c["text"],
            "metadata": {**c["metadata"], "score": round(_cosine(query_emb, c["embedding"]), 4)},
        }
        for c in top
    ]


@traceable(name="generate_answer", run_type="llm")
def _generate(question: str, docs: list[dict]) -> str:
    context_text = "\n\n".join(
        f"[{d['metadata'].get('name', 'unknown')}]\n{d['page_content']}" for d in docs
    )
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Food data:\n{context_text}\n\nQuestion: {question}"}],
    )
    return message.content[0].text


@traceable(name="rag_query", run_type="chain")
def _rag(question: str) -> dict:
    query_emb = _embed(question)
    docs = _retrieve(query_emb)
    answer = _generate(question, docs)
    sources = [d["metadata"].get("name", "") for d in docs if d["metadata"].get("name")]
    return {"answer": answer, "sources": sources}


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        question = (body.get("question") or "").strip()
        if not question:
            return _response(400, json.dumps({"error": "question is required"}))
        if len(question) > 500:
            return _response(400, json.dumps({"error": "question too long (max 500 chars)"}))

        result = _rag(question)
        return _response(200, json.dumps(result))

    except Exception as e:
        print(f"RAG handler error: {e}")
        return _response(500, json.dumps({"error": "Internal server error"}))


def _response(status_code: int, body: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": body,
    }

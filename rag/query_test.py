"""
Quick sanity check: embed a question and retrieve top matching chunks from embeddings.json.

Usage:
    python rag/query_test.py "cheap plant protein"
    python rag/query_test.py "low water use grain"
"""

import json
import math
import os
import pathlib
import sys

import voyageai

EMBEDDINGS_FILE = pathlib.Path(__file__).parent / "embeddings.json"
EMBED_MODEL = "voyage-4"
TOP_K = 3


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def main():
    question = " ".join(sys.argv[1:]) or "cheap high protein food"
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        print("Error: VOYAGE_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    if not EMBEDDINGS_FILE.exists():
        print(f"Error: {EMBEDDINGS_FILE} not found. Run embed_and_store.py first.", file=sys.stderr)
        sys.exit(1)

    with open(EMBEDDINGS_FILE) as f:
        store = json.load(f)

    chunks = store["chunks"]

    client = voyageai.Client(api_key=api_key)
    query_embedding = client.embed([question], model=EMBED_MODEL, input_type="query").embeddings[0]

    scored = sorted(
        chunks,
        key=lambda c: cosine_similarity(query_embedding, c["embedding"]),
        reverse=True,
    )

    print(f'Query: "{question}"\n')
    for i, chunk in enumerate(scored[:TOP_K]):
        score = cosine_similarity(query_embedding, chunk["embedding"])
        print(f"Result {i+1} — {chunk['metadata'].get('name', '?')} (score: {score:.3f})")
        print(chunk["text"][:300])
        print()


if __name__ == "__main__":
    main()

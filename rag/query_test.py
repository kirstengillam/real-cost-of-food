"""
Quick sanity check: embed a question and retrieve top matching chunks from Chroma.

Usage:
    python rag/query_test.py "cheap plant protein"
    python rag/query_test.py "low water use grain"
"""

import os
import sys
import pathlib

import chromadb
import voyageai

CHROMA_DIR = pathlib.Path(__file__).parent / "chroma_db"
EMBED_MODEL = "voyage-4"
COLLECTION_NAME = "real_cost_of_food"
TOP_K = 3


def main():
    question = " ".join(sys.argv[1:]) or "cheap high protein food"
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        print("Error: VOYAGE_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    client = voyageai.Client(api_key=api_key)
    result = client.embed([question], model=EMBED_MODEL, input_type="query")
    query_embedding = result.embeddings[0]

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_collection(COLLECTION_NAME)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    print(f'Query: "{question}"\n')
    for i, (doc, meta, dist) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
    ):
        print(f"Result {i+1} — {meta['name']} (score: {1 - dist:.3f})")
        print(doc[:300])
        print()


if __name__ == "__main__":
    main()

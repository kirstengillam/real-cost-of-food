"""
Phase 2: Embed chunks and store in a local Chroma vector database.

Reads rag/chunks.json (produced by build_chunks.py), embeds each chunk's
text using the Voyage AI API, and persists the collection to rag/chroma_db/.

Re-running this script is safe — it clears and rebuilds the collection each time,
so it stays in sync if chunks.json is regenerated after an ETL run.

Usage:
    export VOYAGE_API_KEY=pa-...
    pip install voyageai chromadb
    python rag/embed_and_store.py
"""

import json
import os
import pathlib
import sys
import time

import chromadb
import voyageai

CHUNKS_FILE = pathlib.Path(__file__).parent / "chunks.json"
CHROMA_DIR = pathlib.Path(__file__).parent / "chroma_db"

EMBED_MODEL = "voyage-4"

COLLECTION_NAME = "real_cost_of_food"

# Voyage rate-limit: embed requests are batched; add a small delay between
# batches to stay well within free-tier limits.
BATCH_SIZE = 16
BATCH_DELAY_SECONDS = 0.5


def get_embeddings(client: voyageai.Client, texts: list[str]) -> list[list[float]]:
    result = client.embed(texts, model=EMBED_MODEL, input_type="document")
    return result.embeddings


def main():
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        print("Error: VOYAGE_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    with open(CHUNKS_FILE) as f:
        export = json.load(f)

    chunks = export["chunks"]
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE}")

    client = voyageai.Client(api_key=api_key)

    # Embed in batches
    all_embeddings = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        print(f"Embedding batch {i // BATCH_SIZE + 1} ({len(texts)} chunks)...")
        embeddings = get_embeddings(client, texts)
        all_embeddings.extend(embeddings)
        if i + BATCH_SIZE < len(chunks):
            time.sleep(BATCH_DELAY_SECONDS)

    print(f"Got {len(all_embeddings)} embeddings (dim={len(all_embeddings[0])})")

    # Store in Chroma
    CHROMA_DIR.mkdir(exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Delete existing collection so re-runs stay in sync
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing '{COLLECTION_NAME}' collection.")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        # Tell Chroma we're supplying our own embeddings
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=all_embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )

    print(f"Stored {collection.count()} items in Chroma at {CHROMA_DIR}")
    print("\nDone. Run a quick sanity check:")
    print('  python rag/query_test.py "cheap plant protein"')
    print("\nNote: set VOYAGE_API_KEY, not ANTHROPIC_API_KEY, for embeddings.")


if __name__ == "__main__":
    main()

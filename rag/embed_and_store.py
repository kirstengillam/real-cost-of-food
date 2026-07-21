"""
Phase 2: Embed chunks and write to rag/embeddings.json.

Reads rag/chunks.json (produced by build_chunks.py), embeds each chunk's
text using the Voyage AI API, and writes the results to rag/embeddings.json.

The deploy-site workflow uploads embeddings.json to S3; the RAG Lambda
fetches it at cold start instead of bundling a Chroma database.

Re-running is safe — embeddings.json is fully overwritten each time.

Usage:
    export VOYAGE_API_KEY=pa-...
    pip install voyageai
    python rag/embed_and_store.py
"""

import json
import os
import pathlib
import sys
import time

import voyageai

CHUNKS_FILE = pathlib.Path(__file__).parent / "chunks.json"
OUTPUT_FILE = pathlib.Path(__file__).parent / "embeddings.json"

EMBED_MODEL = "voyage-4"

BATCH_SIZE = 16
BATCH_DELAY_SECONDS = 0.5


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

    all_embeddings = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        print(f"Embedding batch {i // BATCH_SIZE + 1} ({len(texts)} chunks)...")
        result = client.embed(texts, model=EMBED_MODEL, input_type="document")
        all_embeddings.extend(result.embeddings)
        if i + BATCH_SIZE < len(chunks):
            time.sleep(BATCH_DELAY_SECONDS)

    print(f"Got {len(all_embeddings)} embeddings (dim={len(all_embeddings[0])})")

    records = [
        {
            "id": c["id"],
            "text": c["text"],
            "embedding": emb,
            "metadata": c["metadata"],
        }
        for c, emb in zip(chunks, all_embeddings)
    ]

    with open(OUTPUT_FILE, "w") as f:
        json.dump({"model": EMBED_MODEL, "chunks": records}, f)

    print(f"Wrote {len(records)} records to {OUTPUT_FILE}")
    print("\nDone. Run a quick sanity check:")
    print('  python rag/query_test.py "cheap plant protein"')


if __name__ == "__main__":
    main()

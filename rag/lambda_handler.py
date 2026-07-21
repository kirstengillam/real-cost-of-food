"""
RAG Q&A Lambda handler.

Receives: POST { "question": "..." }
Returns:  { "answer": "...", "sources": [...food names...] }

chroma_db/ is bundled into the Lambda zip at deploy time by the
deploy-site.yml workflow, which runs embed_and_store.py first.
"""

import json
import os
import pathlib

import anthropic
import chromadb
import voyageai

CHROMA_DIR = pathlib.Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "real_cost_of_food"
EMBED_MODEL = "voyage-4"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
TOP_K = 4

SYSTEM_PROMPT = (
    "You are a helpful assistant for Real Cost of Food, a site that tracks grocery "
    "prices, nutrition, and sustainability data sourced from BLS and USDA.\n\n"
    "Answer the user's question using ONLY the food data provided below. "
    "Be specific — cite actual numbers from the data when relevant. "
    "If the data doesn't cover what they're asking, say so explicitly rather than guessing. "
    "Never make up prices, nutrition figures, or sustainability ratings."
)


def handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return _response(200, "")

    try:
        body = json.loads(event.get("body") or "{}")
        question = (body.get("question") or "").strip()
        if not question:
            return _response(400, json.dumps({"error": "question is required"}))
        if len(question) > 500:
            return _response(400, json.dumps({"error": "question too long (max 500 chars)"}))

        if not CHROMA_DIR.exists():
            return _response(503, json.dumps({"error": "Search index not yet built. Try again after the next deploy."}))

        voyage_key = os.environ["VOYAGE_API_KEY"]
        anthropic_key = os.environ["ANTHROPIC_API_KEY"]

        # Embed the question
        vo = voyageai.Client(api_key=voyage_key)
        query_embedding = vo.embed([question], model=EMBED_MODEL, input_type="query").embeddings[0]

        # Retrieve top chunks from Chroma
        chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = chroma.get_collection(COLLECTION_NAME)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K,
            include=["documents", "metadatas"],
        )

        chunks = results["documents"][0]
        metas = results["metadatas"][0]
        sources = [m.get("name", "") for m in metas if m.get("name")]

        context_text = "\n\n".join(
            f"[{meta.get('name', 'unknown')}]\n{doc}"
            for doc, meta in zip(chunks, metas)
        )

        # Generate answer
        client = anthropic.Anthropic(api_key=anthropic_key)
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Food data:\n{context_text}\n\nQuestion: {question}",
                }
            ],
        )

        answer = message.content[0].text
        return _response(200, json.dumps({"answer": answer, "sources": sources}))

    except Exception as e:
        print(f"RAG handler error: {e}")
        return _response(500, json.dumps({"error": "Internal server error"}))


def _response(status_code: int, body: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": body,
    }

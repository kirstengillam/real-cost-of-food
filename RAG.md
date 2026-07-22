# Real Cost of Food — RAG Q&A Add-On

## Purpose

Add a natural-language Q&A feature to Real Cost of Food that lets users ask questions like "what's a cheap plant protein alternative to chicken?" and get answers grounded in the site's actual nutrition/price/sustainability dataset — not a generic LLM guess.

This serves the "honesty over precision" design commitment already core to
the project — answers are constrained to retrieved data, and the system
says so explicitly when something isn't covered, rather than letting the
model hallucinate a number.

## Architecture (v1, kept minimal)

1. **Chunk and embed existing data** — take nutrition/price/sustainability records (currently in SQLite/flat JSON) and turn each item or category into a short text chunk (e.g. "Lentils: $X/lb, Y g protein per dollar, sustainability tier Z").
2. **Vector store** — Chroma, run locally or embedded in the existing static-site build process. Free, simple, no hosted DB needed at this scale.
3. **Retrieval** — embed the user's question, pull the top few matching chunks.
4. **Generation** — pass those chunks + the question to an LLM (Claude via API) with a tight system prompt: *answer only using the provided data; if the data doesn't cover it, say so explicitly.*
5. **Frontend** — a simple text box on the Astro site, calling a small serverless function (AWS Lambda, consistent with existing infra) that handles retrieval + generation.

## Scope guardrails for v1

- **No fine-tuning.** Pure RAG is enough to demonstrate the skill and keeps cost near zero.
- **One dataset category first** (e.g. protein sources), not the full catalog. Ship something working before expanding.
- **No LangChain/LangGraph yet.** Plain API calls (embed → query → generate) for v1 — clearer for portfolio purposes since it shows understanding of what's happening underneath. Add an orchestration framework later if the pipeline's complexity actually warrants it.
- **Optional stretch (not v1):** log queries and add LangSmith tracing, for a taste of LLM-specific observability.

## What this demonstrates

- Chroma → vector database / embedding retrieval
- Retrieval/generation split → the core RAG pattern
- Lambda + API → a real deployment pipeline for an AI feature, not just a static site
- (Stretch) LangSmith → LLM-specific observability/tracing

## Rough time estimate

A working v1 (single category, no tracing, basic frontend) — a few focused evenings, or one weekend for a polished demo.
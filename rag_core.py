import os
import json
from typing import List, Set
from openai import OpenAI
import faiss
import pickle
import numpy as np


# ---------------- PATHS ----------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

GRAPH_FILE = os.path.join(PROCESSED_DIR, "document_graph.json")
PAGE_MAP_FILE = os.path.join(PROCESSED_DIR, "page_map.json")
INDEX_FILE = os.path.join(PROCESSED_DIR, "index.faiss")
PKL_FILE = os.path.join(PROCESSED_DIR, "index.pkl")
FIGURES_FILE = os.path.join(PROCESSED_DIR, "figures.json")


# ---------------- LOAD DATA ----------------
index = faiss.read_index(INDEX_FILE)

with open(PKL_FILE, "rb") as f:
    docstore, index_to_docstore_id = pickle.load(f)

with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph = json.load(f)

with open(PAGE_MAP_FILE, "r", encoding="utf-8") as f:
    page_map = json.load(f)

with open(FIGURES_FILE, "r", encoding="utf-8") as f:
    figures = json.load(f)

nodes = graph["nodes"]
edges = graph["edges"]


# ---------------- LLM CLIENT ----------------
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)


# ---------------- EMBEDDING ----------------
def embed_query(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-qwen3-embedding-8b",
        input=text
    )
    return np.array(response.data[0].embedding, dtype="float32")


# ---------------- SEMANTIC SEARCH ----------------
def find_clauses_semantic(query: str, top_k: int = 5) -> Set[str]:
    query_vec = embed_query(query).reshape(1, -1)
    _, indices = index.search(query_vec, top_k)

    clause_ids = set()

    for idx in indices[0]:
        doc_id = index_to_docstore_id.get(idx)
        if not doc_id:
            continue

        doc = docstore.search(doc_id)
        if not doc:
            continue

        # ✅ CORRECT KEY
        section = doc.metadata.get("section")
        if section:
            clause_ids.add(section)

    return clause_ids


# ---------------- FIGURE RETRIEVAL ----------------
def retrieve_related_figures(clause_ids: Set[str]) -> List[dict]:
    return [
        fig for fig in figures
        if set(fig.get("linked_clauses", [])) & clause_ids
    ]


# ---------------- GRAPH EXPANSION ----------------
def expand_context(start_nodes: Set[str], depth: int = 1) -> Set[str]:
    context = set(start_nodes)

    for _ in range(depth):
        new_nodes = set()
        for edge in edges:
            if edge["from"] in context:
                new_nodes.add(edge["to"])
            if edge["to"] in context:
                new_nodes.add(edge["from"])
        context |= new_nodes

    return context


# ---------------- PAGE RESOLUTION ----------------
def resolve_document_page(pdf_page: int) -> str:
    return page_map.get(str(pdf_page), str(pdf_page))


# ---------------- CONTEXT BUILDERS ----------------
def build_clause_context(clause_ids: Set[str]) -> str:
    parts = []

    for cid in sorted(clause_ids):
        node = nodes.get(cid)
        if not node:
            continue

        doc_page = resolve_document_page(node["page"])
        parts.append(
            f"Clause {cid} (Document page {doc_page}):\n{node['text']}"
        )

    return "\n\n".join(parts)


def build_figure_context(figs: List[dict]) -> str:
    blocks = []

    for fig in figs:
        summary = fig.get("ocr_text", "").strip()
        if len(summary) > 300:
            summary = summary[:300] + "..."

        blocks.append(
            f"Figure {fig['figure_id']} (Document page {fig['doc_page']}):\n"
            f"OCR summary:\n{summary}\n"
            f"Linked clauses: {', '.join(fig.get('linked_clauses', []))}\n"
            f"Linked tables: {', '.join(fig.get('linked_tables', []))}"
        )

    return "\n\n".join(blocks)


# ---------------- PROMPT ----------------
def build_prompt(question: str, context: str) -> str:
    return f"""
You are answering strictly from an Indian Standard document (IS 456).

Answer Format (MANDATORY):
- Start with a one-sentence direct answer.
- Then list supporting clauses as bullet points.
- Each bullet point MUST include:
  - Clause number
  - Document page number
  - A brief excerpt or paraphrase

Rules:
- Use ONLY the information provided
- Do NOT add external knowledge
- Do NOT guess or infer
- Do NOT modify page references
- If information is missing, explicitly state it

Question:
{question}

Context:
{context}
"""


# ---------------- LLM CALL ----------------
def ask_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": "You are a strict IS 456 assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.15,
        max_tokens=1024
    )
    return response.choices[0].message.content


# ---------------- MAIN ENTRY ----------------
def answer_question(query: str) -> str:
    clause_ids = find_clauses_semantic(query)

    if not clause_ids:
        return "No relevant clauses found for this question."

    expanded = expand_context(clause_ids, depth=1)
    figures_ctx = retrieve_related_figures(expanded)

    clause_context = build_clause_context(clause_ids)
    figure_context = build_figure_context(figures_ctx)

    full_context = clause_context
    if figure_context:
        full_context += "\n\n--- RELATED FIGURES ---\n\n" + figure_context

    prompt = build_prompt(query, full_context)
    return ask_llm(prompt)
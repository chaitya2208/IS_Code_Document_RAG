import os
import json
import faiss
import pickle
import numpy as np
from typing import List, Set
from openai import OpenAI

# ---------------- PATHS ----------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

GRAPH_FILE = os.path.join(PROCESSED_DIR, "document_graph.json")
PAGE_MAP_FILE = os.path.join(PROCESSED_DIR, "page_map.json")
INDEX_FILE = os.path.join(PROCESSED_DIR, "index.faiss")
PKL_FILE = os.path.join(PROCESSED_DIR, "index.pkl")


# ---------------- LOAD ----------------
index = faiss.read_index(INDEX_FILE)

with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph = json.load(f)

with open(PAGE_MAP_FILE, "r", encoding="utf-8") as f:
    page_map = json.load(f)

with open(PKL_FILE, "rb") as f:
    docstore, index_to_docstore_id = pickle.load(f)

with open("/Users/chaityashah/Downloads/RMS/IS_code_RAG_LLM_latest/data/processed/figures_final.json", "r", encoding="utf-8") as f:
    figures_data = json.load(f)

nodes = graph["nodes"]

# ---------------- LLM CLIENT ----------------
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# ---------------- EMBEDDING ----------------
def embed_query(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-qwen3-embedding-8b",
        input=text
    )
    return np.array(response.data[0].embedding, dtype="float32")

# ---------------- CLAUSE RETRIEVAL ----------------
def find_clauses_semantic(query: str, top_k=5) -> Set[str]:
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

        section = doc.metadata.get("section")
        if section:
            clause_ids.add(section)

    return clause_ids

# ---------------- CLAUSE CLEANING ----------------
def remove_generic_clauses(clauses: Set[str]) -> Set[str]:
    return {c for c in clauses if len(c.split(".")) > 1}

def add_parent_clauses(clauses: Set[str]) -> Set[str]:
    expanded = set(clauses)
    for c in clauses:
        parts = c.split(".")
        for i in range(1, len(parts)):
            expanded.add(".".join(parts[:i]))
    return expanded

# ---------------- BUILD CLAUSE CONTEXT ----------------
def resolve_document_page(pdf_page: int) -> str:
    return page_map.get(str(pdf_page), f"PDF-{pdf_page}")

def build_clause_context(clause_ids: Set[str]) -> str:
    parts = []

    for cid in sorted(clause_ids):
        for node in nodes.values():
            if node.get("clause_id") == cid:
                page = resolve_document_page(node["page"])
                parts.append(
                    f"Clause {cid} (Document Page: {page}): {node['text'][:400]}"
                )
                break

    return "\n\n".join(parts)

# ---------------- VISUAL QUERY DETECTION ----------------
def is_visual_query(query: str) -> bool:
    query = query.lower()
    keywords = [
        "figure", "diagram", "image", "sketch",
        "reinforcement", "detail", "layout", "drawing"
    ]
    return any(k in query for k in keywords)

# ---------------- COSINE SIM ----------------
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# ---------------- FIGURE RETRIEVAL ----------------
def find_relevant_figures_semantic(query: str, figures: list, top_k=2):
    query_vec = np.array(embed_query(query)).reshape(1, -1)

    scored = []

    for fig in figures:
        desc = fig.get("description", "")

        if not desc or "embedding" not in fig:
            continue

        desc_vec = np.array(fig["embedding"]).reshape(1, -1)

        sim = float(np.dot(query_vec, desc_vec.T))

        if sim > 0.45:
            scored.append((sim, fig))

    scored.sort(reverse=True, key=lambda x: x[0])

    return [f for s, f in scored[:top_k]]

# ---------------- FIGURE CONTEXT ----------------
def build_figure_context(figures):
    context = ""

    for fig in figures:
        desc = fig.get("description", "")
        desc = desc[:300] if desc else ""

        context += f"""
Figure: {fig.get("figure_id")}

Meaning:
{desc}
"""

    return context

# ---------------- PROMPT ----------------
def build_prompt(question: str, context: str) -> str:
    return f"""
You are an expert assistant for IS 456.

- First explain the answer in simple terms
- Then give supporting clauses (with clause number + page)
- Use ONLY given context

Question:
{question}

Context:
{context}
"""

# ---------------- LLM ----------------
def ask_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": "You are an IS 456 assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=800
    )
    return response.choices[0].message.content

# ---------------- MAIN ----------------
def answer_question(query: str):
    clauses = find_clauses_semantic(query)

    if not clauses:
        return "No relevant clauses found.", []

    clauses = remove_generic_clauses(clauses)
    clauses = add_parent_clauses(clauses)

    clause_context = build_clause_context(clauses)

    related_figures = []
    if is_visual_query(query):
        related_figures = find_relevant_figures_semantic(query, figures_data)

    figure_context = build_figure_context(related_figures)

    full_context = clause_context
    if figure_context:
        full_context += "\n\n--- FIGURES ---\n\n" + figure_context

    answer = ask_llm(build_prompt(query, full_context))

    print("QUERY:", query)
    print("IS VISUAL:", is_visual_query(query))

    return answer, related_figures
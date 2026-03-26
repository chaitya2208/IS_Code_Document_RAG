import os
import json
from typing import List
from langchain_openai import ChatOpenAI



PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
GRAPH_FILE = os.path.join(PROCESSED_DIR, "document_graph.json")
PAGE_MAP_FILE = os.path.join(PROCESSED_DIR, "page_map.json")




with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph = json.load(f)

with open(PAGE_MAP_FILE, "r", encoding="utf-8") as f:
    page_map = json.load(f)

nodes = graph["nodes"]
edges = graph["edges"]



def find_clauses_by_keyword(keyword: str) -> List[str]:
    keyword = keyword.lower()
    return [
        node_id
        for node_id, node in nodes.items()
        if node["type"] == "clause" and keyword in node["text"].lower()
    ]


def expand_context(start_nodes: List[str], depth=1):
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




def build_context_text(node_ids: set) -> str:
    parts = []

    for nid in sorted(node_ids):  
        node = nodes.get(nid)
        if not node:
            continue

        doc_page = page_map.get(str(node["page"]), f"PDF-{node['page']}")


        if node["type"] == "clause":
            parts.append(
                f"Clause {node['clause_id']} (Document page {doc_page}):\n{node['text']}"
            )
        elif node["type"] == "table":
            parts.append(
                f"Table on Document page {doc_page} with columns {node['columns']}"
            )

    return "\n\n".join(parts)


def filter_relevant_nodes(query: str, node_ids: set):
    query_terms = set(query.lower().split())
    filtered = set()

    for nid in node_ids:
        node = nodes.get(nid)
        if node and node["type"] == "clause":
            if query_terms & set(node["text"].lower().split()):
                filtered.add(nid)

    return filtered




def build_prompt(question: str, context: str) -> str:
    return f"""
You are answering strictly from an Indian Standard document (IS 456).

FORMAT:
- One-line direct answer
- Bullet points explaining relevant clauses
- Do NOT enumerate or name items unless explicitly listed in the context

Rules:
- Use ONLY the information provided in the context
- Do NOT add external knowledge
- Do NOT guess or infer beyond the text
- Always mention clause numbers and PDF page numbers
- If a clause mentions items without listing them, state that they are defined but not detailed in the provided context.


Question:
{question}

Context:
{context}

Write a clear, structured answer.
"""




llm = ChatOpenAI(
    openai_api_base="http://localhost:1234/v1",
    openai_api_key="lm-studio",
    model="llama-3.1-8b-instruct",
    temperature=0.15,
)



def ask_llm(prompt: str) -> str:
    response = llm.invoke(prompt)
    return response.content




if __name__ == "__main__":
    query = input("Ask a question: ")

    seed_clauses = find_clauses_by_keyword(query)
    if not seed_clauses:
        print("No relevant clauses found.")
        exit()

    expanded_nodes = expand_context(seed_clauses, depth=1)
    filtered_clauses = filter_relevant_nodes(query, expanded_nodes)

    final_context_nodes = set(filtered_clauses)
    for edge in edges:
        if edge["type"] == "REFERS_TO":
            if edge["from"] in filtered_clauses:
                final_context_nodes.add(edge["to"])
            if edge["to"] in filtered_clauses:
                final_context_nodes.add(edge["from"])

    context_text = build_context_text(final_context_nodes)
    prompt = build_prompt(query, context_text)

    answer = ask_llm(prompt)

    print("\n--- FINAL ANSWER ---\n")
    print(answer)


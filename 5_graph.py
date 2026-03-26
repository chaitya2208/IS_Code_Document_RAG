import os
import json
from typing import Dict, List


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

CLAUSES_FILE = os.path.join(PROCESSED_DIR, "clauses.json")
TABLES_FILE = os.path.join(PROCESSED_DIR, "tables.json")
LINKS_FILE = os.path.join(PROCESSED_DIR, "clause_table_links.json")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "document_graph.json")


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


clauses = load_json(CLAUSES_FILE)
tables = load_json(TABLES_FILE)
links = load_json(LINKS_FILE)


graph = {
    "nodes": {},
    "edges": []
}


for clause in clauses:
    graph["nodes"][f"clause:{clause['clause_id']}"] = {
        "type": "clause",
        "clause_id": clause["clause_id"],
        "text": clause["text"],
        "page": clause["page"]
    }


for table in tables:
    graph["nodes"][f"table:{table['table_id']}"] = {
        "type": "table",
        "table_id": table["table_id"],
        "page": table["page"],
        "columns": table["columns"]
    }


for clause in clauses:
    if clause["parent"]:
        graph["edges"].append({
            "from": f"clause:{clause['parent']}",
            "to": f"clause:{clause['clause_id']}",
            "type": "PARENT_OF"
        })


for link in links:
    graph["edges"].append({
        "from": f"clause:{link['from_clause']}",
        "to": link["to_table"],  # symbolic for now
        "type": "REFERS_TO",
        "page": link["page"]
    })


with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(graph, f, indent=2)

print(f"Graph saved to: {OUTPUT_FILE}")
print(f"Total nodes: {len(graph['nodes'])}")
print(f"Total edges: {len(graph['edges'])}")


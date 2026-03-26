import os
import json
import re
from typing import Dict, List



PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

CLAUSES_FILE = os.path.join(PROCESSED_DIR, "clauses.json")
TABLES_FILE = os.path.join(PROCESSED_DIR, "tables.json")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "clause_table_links.json")




def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


clauses = load_json(CLAUSES_FILE)
tables = load_json(TABLES_FILE)  




TABLE_REF_REGEX = re.compile(r"\bTable\s+(\d+)\b", re.IGNORECASE)
CLAUSE_REF_REGEX = re.compile(r"\bClause\s+(\d+(\.\d+)*)\b", re.IGNORECASE)




def extract_references(text: str):
    table_refs = TABLE_REF_REGEX.findall(text)
    clause_refs = CLAUSE_REF_REGEX.findall(text)

    return {
        "tables": [f"Table {t}" for t in table_refs],
        "clauses": [c[0] for c in clause_refs]
    }




def build_links(clauses: List[Dict]) -> List[Dict]:
    links = []
    seen = set()

    for clause in clauses:
        refs = extract_references(clause["text"])

        for table_ref in refs["tables"]:
            key = (clause["clause_id"], table_ref)
            if key in seen:
                continue

            seen.add(key)
            links.append({
                "from_clause": clause["clause_id"],
                "to_table": table_ref,
                "page": clause["page"]
            })


    links.sort(key=lambda x: (x["from_clause"], x["to_table"]))
    return links



def save_links(links: List[Dict], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2)


def inspect_links(links: List[Dict], limit=10):
    print("\n--- SAMPLE CLAUSE ↔ TABLE LINKS ---")
    for link in links[:limit]:
        print(link)



if __name__ == "__main__":
    clause_table_links = build_links(clauses)
    save_links(clause_table_links, OUTPUT_FILE)

    print(f"Total links found: {len(clause_table_links)}")
    print(f"Saved to: {OUTPUT_FILE}")

    inspect_links(clause_table_links)

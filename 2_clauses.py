from pydantic import BaseModel, Field
from typing import Optional, List
from unstructured.partition.pdf import partition_pdf
import re
import os
import json



PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

PDF_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "pdf",
    "IS_456_Preliminary_Draft.pdf"
)

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

CLAUSES_OUTPUT_FILE = os.path.join(PROCESSED_DIR, "clauses.json")



def ingest_pdf(pdf_path: str):
    return partition_pdf(
        filename=pdf_path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_images_in_pdf=False
    )



class Clause(BaseModel):
    clause_id: str
    title: Optional[str]
    text: str
    page: int
    parent: Optional[str] = None
    children: List[str] = Field(default_factory=list)



CLAUSE_REGEX = re.compile(r"^(\d+(\.\d+)+|\d+)\s")


def extract_clause_id(text: str):
    match = CLAUSE_REGEX.match(text.strip())
    return match.group(1) if match else None


def extract_clauses(elements):
    clauses = []
    seen = set()

    for el in elements:
        if el.category == "NarrativeText":
            clause_id = extract_clause_id(el.text)
            if clause_id and clause_id not in seen:
                seen.add(clause_id)
                clauses.append(
                    Clause(
                        clause_id=clause_id,
                        title=None,
                        text=el.text.strip(),
                        page=el.metadata.page_number
                    )
                )

    return clauses



def get_parent_clause(clause_id: str):
    if "." not in clause_id:
        return None
    return ".".join(clause_id.split(".")[:-1])


def build_hierarchy(clauses):
    clause_map = {c.clause_id: c for c in clauses}

    for clause in clauses:
        parent_id = get_parent_clause(clause.clause_id)
        clause.parent = parent_id

        if parent_id and parent_id in clause_map:
            clause_map[parent_id].children.append(clause.clause_id)

    return clause_map



def inspect_clauses(clause_map, limit=10):
    print("\n--- SAMPLE CLAUSES ---")
    for i, cid in enumerate(sorted(clause_map)):
        if i >= limit:
            break
        clause = clause_map[cid]
        print("=" * 60)
        print(f"Clause ID: {clause.clause_id}")
        print(f"Parent   : {clause.parent}")
        print(f"Children : {clause.children}")
        print(f"Page     : {clause.page}")
        print(f"Text     : {clause.text[:300]}")



def serialize_clauses(clause_map):
    serialized = []

    for clause in clause_map.values():
        serialized.append({
            "clause_id": clause.clause_id,
            "text": clause.text,
            "page": clause.page,
            "parent": clause.parent,
            "children": clause.children
        })

    return serialized



if __name__ == "__main__":
    elements = ingest_pdf(PDF_PATH)
    clauses = extract_clauses(elements)
    clause_map = build_hierarchy(clauses)

    inspect_clauses(clause_map)

    serialized_clauses = serialize_clauses(clause_map)

    with open(CLAUSES_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(serialized_clauses, f, indent=2)

    print(f"\nSaved clauses to: {CLAUSES_OUTPUT_FILE}")
    print(f"Total clauses saved: {len(serialized_clauses)}")

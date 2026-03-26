import os
import json
import uuid
from typing import List
from pydantic import BaseModel
from unstructured.partition.pdf import partition_pdf
from bs4 import BeautifulSoup

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(DATA_DIR, "processed")
PDF_PATH = os.path.join(DATA_DIR, "pdf", "IS_456_Preliminary_Draft.pdf")

os.makedirs(OUTPUT_DIR, exist_ok=True)

class TableRow(BaseModel):
    row_id: str
    cells: dict


class Table(BaseModel):
    table_id: str
    title: str | None
    page: int
    columns: List[str]
    rows: List[TableRow]


def ingest_pdf(pdf_path: str):
    return partition_pdf(
        filename=pdf_path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_images_in_pdf=False
    )


def parse_tables(elements) -> List[Table]:
    tables: List[Table] = []

    for el in elements:
        if el.category != "Table":
            continue

        html = el.metadata.text_as_html
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        rows = soup.find_all("tr")
        if len(rows) < 2:
            continue

        headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
        if not headers:
            continue

        table_rows = []
        for r in rows[1:]:
            cells = [td.get_text(strip=True) for td in r.find_all(["td", "th"])]
            if len(cells) != len(headers):
                continue

            table_rows.append(
                TableRow(
                    row_id=str(uuid.uuid4()),
                    cells=dict(zip(headers, cells))
                )
            )

        if table_rows:
            tables.append(
                Table(
                    table_id=f"table_{uuid.uuid4().hex[:8]}",
                    title=None,
                    page=el.metadata.page_number,
                    columns=headers,
                    rows=table_rows
                )
            )

    return tables


def save_tables(tables: List[Table], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([t.model_dump() for t in tables], f, indent=2)



def inspect_tables(tables: List[Table], limit=2):
    print("\n--- SAMPLE TABLES ---")
    for t in tables[:limit]:
        print("=" * 70)
        print(f"Table ID : {t.table_id}")
        print(f"Page     : {t.page}")
        print(f"Columns  : {t.columns}")
        print("First row:")
        print(t.rows[0].cells)


if __name__ == "__main__":
    elements = ingest_pdf(PDF_PATH)
    tables = parse_tables(elements)

    output_file = os.path.join(OUTPUT_DIR, "tables.json")
    save_tables(tables, output_file)

    print(f"\nTotal tables extracted: {len(tables)}")
    print(f"Saved to: {output_file}")

    inspect_tables(tables)


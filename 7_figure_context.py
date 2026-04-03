import json
from collections import defaultdict
from unstructured.partition.pdf import partition_pdf
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(PROJECT_ROOT, "data/pdf/IS_456_Preliminary_Draft.pdf")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

FIGURES_FILE = os.path.join(PROCESSED_DIR, "figures.json")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "figures.json")  # overwrite


def ingest_elements():
    return partition_pdf(
        filename=PDF_PATH,
        strategy="hi_res",
        infer_table_structure=True,
        extract_images_in_pdf=False,
    )


def group_text_by_page(elements):
    page_text = defaultdict(list)

    for el in elements:
        if hasattr(el, "text") and el.text and el.metadata.page_number:
            page_text[el.metadata.page_number].append(el.text.strip())

    return page_text


def attach_context():
    with open(FIGURES_FILE, "r", encoding="utf-8") as f:
        figures = json.load(f)

    elements = ingest_elements()
    page_text = group_text_by_page(elements)

    for fig in figures:
        p = fig["pdf_page"]

        fig["context_text"] = {
            "previous_page": "\n".join(page_text.get(p - 1, [])),
            "same_page": "\n".join(page_text.get(p, [])),
            "next_page": "\n".join(page_text.get(p + 1, [])),
        }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(figures, f, indent=2)

    print("Figure context attached successfully.")


if __name__ == "__main__":
    attach_context()

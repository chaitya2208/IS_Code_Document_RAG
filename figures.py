import os
import json
import pytesseract
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FIGURE_DIR = os.path.join(PROJECT_ROOT, "figures")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

PAGE_MAP_FILE = os.path.join(PROCESSED_DIR, "page_map.json")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "figures.json")

with open(PAGE_MAP_FILE, "r", encoding="utf-8") as f:
    page_map = json.load(f)


def ocr_image(image_path):
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img, lang="eng").strip()
    except:
        return ""


def build_figures():
    figures = []

    for fname in os.listdir(FIGURE_DIR):
        if not fname.startswith("figure-"):
            continue

        # figure-18-4.jpg
        parts = fname.replace(".jpg", "").split("-")
        pdf_page = int(parts[1])
        fig_idx = int(parts[2])

        doc_page = page_map.get(str(pdf_page), None)

        image_path = os.path.join(FIGURE_DIR, fname)
        ocr_text = ocr_image(image_path)

        figures.append({
            "figure_id": f"Fig-{pdf_page}-{fig_idx}",
            "pdf_page": pdf_page,
            "doc_page": doc_page,
            "figure_index_on_page": fig_idx,
            "image_path": image_path,
            "ocr_text": ocr_text,
            "context_text": {},
            "linked_clauses": [],
            "linked_tables": [],
            "type": "figure"
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(figures, f, indent=2)

    print(f"Saved {len(figures)} figures to {OUTPUT_FILE}")


if __name__ == "__main__":
    build_figures()

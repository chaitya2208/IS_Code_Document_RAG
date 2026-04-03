import os
import json
import re
import pdfplumber

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(PROJECT_ROOT, "data/pdf/IS_456_Preliminary_Draft.pdf")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data/processed/page_map.json")

PAGE_NUMBER_REGEX = re.compile(r"^\s*(\d+|[ivxlcdm]+)\s*$", re.IGNORECASE)

def extract_page_map(pdf_path: str):
    page_map = {}

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            # Check last few lines (footer)
            for line in reversed(lines[-5:]):
                match = PAGE_NUMBER_REGEX.match(line)
                if match:
                    page_map[str(i)] = match.group(1)
                    break

    return page_map


if __name__ == "__main__":
    page_map = extract_page_map(PDF_PATH)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(page_map, f, indent=2)

    print(f"Saved page map to: {OUTPUT_FILE}")
    print(f"Total mapped pages: {len(page_map)}")

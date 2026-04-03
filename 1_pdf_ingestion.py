from unstructured.partition.pdf import partition_pdf
import os
import json

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(PROJECT_ROOT, "data/pdf/IS_456_Preliminary_Draft.pdf")
OUT_FILE = os.path.join(PROJECT_ROOT, "data/processed/elements_ocr.json")

elements = partition_pdf(
    filename=PDF_PATH,
    strategy="hi_res",
    infer_table_structure=True,
    extract_images_in_pdf=True,
    ocr_languages="eng"
)

serialized = []
for el in elements:
    serialized.append({
        "type": el.category,
        "text": el.text,
        "metadata": el.metadata.to_dict()
    })

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(serialized, f, indent=2)

print(f"Extracted {len(serialized)} elements with OCR")

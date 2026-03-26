# from unstructured.partition.pdf import partition_pdf
# from collections import Counter
# import os

# PDF_PATH = os.path.join(os.path.dirname(__file__), "data/pdf/IS_456_Preliminary_Draft.pdf")


# def ingest_pdf(pdf_path: str):
#     elements = partition_pdf(
#         filename=pdf_path,
#         strategy="hi_res",
#         infer_table_structure=True,
#         extract_images_in_pdf=False,
#     )
#     return elements


# def inspect_elements(elements):
#     print("\n--- ELEMENT TYPE COUNTS ---")
#     counts = Counter(type(el).__name__ for el in elements)
#     for k, v in counts.items():
#         print(f"{k}: {v}")

#     print("\n--- SAMPLE ELEMENTS ---")
#     for el in elements[:5]:
#         print("=" * 60)
#         print("TYPE:", type(el).__name__)
#         print("PAGE:", el.metadata.page_number)
#         print("TEXT PREVIEW:")
#         print(el.text[:500])


# if __name__ == "__main__":
#     elements = ingest_pdf(PDF_PATH)
#     inspect_elements(elements)



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

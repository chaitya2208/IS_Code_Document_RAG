import os
import json
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

FIGURES_FILE = os.path.join(PROCESSED_DIR, "figures.json")

CLAUSE_REGEX = re.compile(
    r"(?<![\d.])"        # no digit or dot before
    r"(?:[1-9]\d*)"      # clause root
    r"(?:\.\d+)+"        # one or more .x
    r"(?!\d)"            # no digit after
)

TABLE_REGEX = re.compile(
    r"\bTable\s+(\d+[A-Z]?)\b",
    re.IGNORECASE
)


def extract_clauses_from_text(text: str) -> set[str]:
    if not text:
        return set()
    return {m.group(0) for m in CLAUSE_REGEX.finditer(text)}


def extract_table_refs_from_context(context_text: dict) -> list[str]:
    tables = set()

    for section in ("previous_page", "same_page", "next_page"):
        text = context_text.get(section, "")
        if not text:
            continue

        for t in TABLE_REGEX.findall(text):
            tables.add(f"Table {t}")

    return sorted(tables)


def link_figures(figures: list[dict]) -> list[dict]:
    for fig in figures:
        context = fig.get("context_text", {})

        linked_clauses = set()
        for section in ("previous_page", "same_page", "next_page"):
            linked_clauses |= extract_clauses_from_text(context.get(section, ""))

        fig["linked_clauses"] = sorted(linked_clauses)
        fig["linked_tables"] = extract_table_refs_from_context(context)

    return figures


if __name__ == "__main__":
    with open(FIGURES_FILE, "r", encoding="utf-8") as f:
        figures = json.load(f)

    figures = link_figures(figures)

    with open(FIGURES_FILE, "w", encoding="utf-8") as f:
        json.dump(figures, f, indent=2)

    print("✅ figures.json updated in-place")
    print(f"📁 File: {FIGURES_FILE}")

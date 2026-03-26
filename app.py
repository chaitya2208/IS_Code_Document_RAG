import streamlit as st
from rag_core import answer_question
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
FIGURES_FILE = os.path.join(PROCESSED_DIR, "figures.json")

with open(FIGURES_FILE, "r", encoding="utf-8") as f:
    FIGURES = json.load(f)


st.set_page_config(
    page_title="IS 456 Intelligent Assistant",
    layout="wide"
)

st.title("📘 IS 456 – Intelligent Assistant")
st.caption("Grounded answers with clauses, pages, tables, and figures")

st.divider()

query = st.text_input("Ask a question from IS 456", placeholder="e.g. load combinations")

if st.button("Ask") and query.strip():
    with st.spinner("Searching IS 456..."):
        answer = answer_question(query)

    st.subheader("✅ Answer")
    st.write(answer)

    # ---------- FIGURES ----------
    related_figures = []
    for fig in FIGURES:
        if any(clause in answer for clause in fig.get("linked_clauses", [])):
            related_figures.append(fig)

    if related_figures:
        st.divider()
        st.subheader("🖼️ Related Figures")

        for fig in related_figures:
            cols = st.columns([1, 2])
            with cols[0]:
                st.image(fig["image_path"], use_column_width=True)
            with cols[1]:
                st.markdown(f"**Figure:** {fig['figure_id']}")
                st.markdown(f"**Document page:** {fig['doc_page']}")
                if fig.get("linked_clauses"):
                    st.markdown(
                        f"**Linked clauses:** {', '.join(fig['linked_clauses'])}"
                    )

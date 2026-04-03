import streamlit as st
import os
from rag_core import answer_question

st.set_page_config(page_title="IS 456 Assistant", layout="wide")

st.title("📘 IS 456 – Intelligent Assistant")

query = st.text_input("Ask a question from IS 456")

if st.button("Ask"):
    if query:
        answer, related_figures = answer_question(query)

        st.markdown("## ✅ Answer")
        st.write(answer)

        if related_figures:
            st.markdown("## 🖼️ Related Figures")

            for fig in related_figures:
                col1, col2 = st.columns([2, 1])

                with col1:
                    img_path = fig.get("image_path")
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                    else:
                        st.warning("Image not found")

                with col2:
                    st.write(f"**Figure:** {fig.get('figure_id')}")
                    st.write(f"**Document page:** {fig.get('doc_page')}")

                    desc = fig.get("description", "")
                    if desc:
                        st.write("**Explanation:**")
                        st.write(desc[:200])
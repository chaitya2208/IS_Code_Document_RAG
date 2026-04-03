import json

# Load both files
with open("/Users/chaityashah/Downloads/RMS/IS_code_RAG_LLM_latest/data/processed/figures.json") as f:
    figures = json.load(f)

with open("/Users/chaityashah/Downloads/RMS/IS_code_RAG_LLM_latest/data/processed/figure_descriptions_lmstudio.json") as f:
    descriptions = json.load(f)

# Create mapping: image_path → description
desc_map = {
    d["image_path"]: d["description"]
    for d in descriptions
}

# Merge
for fig in figures:
    path = fig.get("image_path")

    if path in desc_map:
        fig["description"] = desc_map[path]

# Save new file
with open("figures_merged.json", "w") as f:
    json.dump(figures, f, indent=2)

print("✅ MERGED FILE CREATED")
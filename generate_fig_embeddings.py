import json
from openai import OpenAI

# LM Studio client
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)

def embed(text):
    response = client.embeddings.create(
        model="text-embedding-qwen3-embedding-8b",
        input=text
    )
    return response.data[0].embedding


# Load merged file
with open("/Users/chaityashah/Downloads/RMS/IS_code_RAG_LLM_latest/data/processed/figures_merged.json") as f:
    figures = json.load(f)

# Generate embeddings
for fig in figures:
    desc = fig.get("description", "")

    if desc:
        print("Embedding:", fig.get("figure_id"))

        # OPTIONAL: shorten (recommended)
        desc = desc[:500]

        fig["embedding"] = embed(desc)

# Save final file
with open("/Users/chaityashah/Downloads/RMS/IS_code_RAG_LLM_latest/data/processed/figures_final.json", "w") as f:
    json.dump(figures, f)

print("✅ Embeddings generated → figures_final.json ready")
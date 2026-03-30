import streamlit as st
from qdrant_client import QdrantClient, models as qdrant_models
# from sentence_transformers import SentenceTransformer
from openai import OpenAI
import requests

# ------------------------------
# Config
# ------------------------------
COLLECTION_NAME = "db-design-bge-large"
TOP_K           = 5
HF_MODEL        = "BAAI/bge-large-en-v1.5"
HF_API_URL = "https://router.huggingface.co/hf-inference/models/BAAI/bge-large-en-v1.5/pipeline/feature-extraction"



# ------------------------------
# Clients
# ------------------------------
@st.cache_resource
def load_clients():
    qdrant = QdrantClient(
        url=st.secrets["qdrant_uri"],
        api_key=st.secrets["qdrant_api_key"]
    )
    openai = OpenAI(api_key=st.secrets["openai_api_key"])
    return qdrant, openai

# ------------------------------
# Embed query via HuggingFace API
# ------------------------------
# def embed_query(query: str) -> list:
#     headers  = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
#     response = requests.post(HF_API_URL, headers=headers, json={"inputs": query})
#     return response.json()


def embed_query(query: str) -> list:
    headers  = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    response = requests.post(HF_API_URL, headers=headers, json={"inputs": query})
    
    if response.status_code != 200:
        raise ValueError(f"HF API failed: {response.status_code} - {response.text}")
    
    if not response.text:
        raise ValueError("HF API returned empty response")
    
    result = response.json()
    if isinstance(result, dict) and "error" in result:
        raise ValueError(f"HuggingFace API error: {result['error']}")
    
    embedding = result
    if isinstance(embedding[0], list):
        embedding = embedding[0]
    return embedding

# ------------------------------
# Hybrid Search
# ------------------------------
def hybrid_search(qdrant, query: str) -> list:
    dense_vector = embed_query(query)
    results      = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            qdrant_models.Prefetch(
                query=qdrant_models.Document(
                    text=query,
                    model="Qdrant/bm25"
                ),
                using="text-sparse",
                limit=20
            ),
            qdrant_models.Prefetch(
                query=dense_vector,
                limit=20
            )
        ],
        query=qdrant_models.FusionQuery(fusion=qdrant_models.Fusion.RRF),
        limit=TOP_K
    )
    return results.points

# ------------------------------
# Build context from chunks
# ------------------------------
def build_context(points: list) -> str:
    context = ""
    for i, point in enumerate(points, 1):
        source = point.payload.get('source_file', 'Unknown')
        page   = point.payload.get('page_number', 'Unknown')
        text   = point.payload.get('page_content', '')
        context += f"[{i}] Source: {source} | Page: {page}\n{text}\n\n"
    return context

# ------------------------------
# Query OpenAI
# ------------------------------
def query_openai(openai, question: str, context: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a database design expert. Answer the question using only the provided context from the reference books. If the answer is not in the context, say so."
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ]
    )
    return response.choices[0].message.content

# ------------------------------
# Streamlit UI
# ------------------------------
st.title("📚 Database Design Assistant")
st.caption("Powered by BGE-Large + Qdrant Hybrid Search + GPT-4o Mini")

qdrant, openai = load_clients()

question = st.text_input("Ask a question about database design:")

if question:
    with st.spinner("Searching..."):
        points  = hybrid_search(qdrant, question)
        context = build_context(points)
        answer  = query_openai(openai, question, context)

    st.markdown("### Answer")
    st.write(answer)

    with st.expander("View source chunks"):
        for i, point in enumerate(points, 1):
            st.markdown(f"**Chunk {i}** | Source: `{point.payload.get('source_file')}` | Page: `{point.payload.get('page_number')}` | Score: `{point.score:.4f}`")
            st.write(point.payload.get('page_content'))
            st.divider()
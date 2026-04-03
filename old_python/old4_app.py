import streamlit as st
from qdrant_client import QdrantClient, models as qdrant_models
from openai import OpenAI
import requests
import pandas as pd

# ------------------------------
# Config
# ------------------------------
COLLECTION_NAME = "db-design-bge-large"
TOP_K           = 5
HF_API_URL      = "https://router.huggingface.co/hf-inference/models/BAAI/bge-large-en-v1.5/pipeline/feature-extraction"

# ------------------------------
# Clients
# ------------------------------
@st.cache_resource
def load_clients():
    qdrant = QdrantClient(
        url=st.secrets["qdrant_uri"],
        api_key=st.secrets["qdrant_api_key"]
    )
    openai_client = OpenAI(
        api_key=st.secrets["openai_api_key"]
    )
    openrouter_client = OpenAI(
        api_key=st.secrets["openrouter_api_key"],
        base_url="https://openrouter.ai/api/v1"
    )
    return qdrant, openai_client, openrouter_client

# ------------------------------
# Load uploaded file into DataFrame
# ------------------------------
def load_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith('.xlsx'):
        return pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith('.json'):
        return pd.read_json(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {uploaded_file.name}")

# ------------------------------
# Build column summary for LLM
# ------------------------------
def build_column_summary(df: pd.DataFrame) -> str:
    summary = "Columns and sample data:\n\n"
    for col in df.columns:
        dtype   = str(df[col].dtype)
        samples = df[col].dropna().head(5).tolist()
        summary += f"- {col} (dtype: {dtype}): {samples}\n"
    return summary

# ------------------------------
# Embed query via HuggingFace API
# ------------------------------
def embed_query(query: str) -> list:
    headers  = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    response = requests.post(HF_API_URL, headers=headers, json={"inputs": query})
    if response.status_code != 200:
        raise ValueError(f"HF API failed: {response.status_code} - {response.text}")
    result = response.json()
    if isinstance(result[0], list):
        result = result[0]
    return result

# ------------------------------
# Hybrid Search
# ------------------------------
def hybrid_search(qdrant, query: str) -> list:
    dense_vector = embed_query(query)
    results      = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            qdrant_models.Prefetch(
                query=qdrant_models.Document(text=query, model="Qdrant/bm25"),
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
# Generate SQL via OpenAI
# ------------------------------
def generate_sql(openai_client, column_summary: str, rag_context: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a senior database architect specialising in star schema design for data warehouses.

Your job is to analyse a flat file's columns and generate SQL Server CREATE TABLE scripts following strict star schema best practices.

DIMENSION RULES:
- Descriptive attributes (names, categories, types, statuses, methods) always go in dimension tables
- Every dimension table must have a surrogate key (INT IDENTITY(1,1) PRIMARY KEY) e.g. CustomerKey
- Keep the natural/business key as a separate column e.g. CustomerID
- Low cardinality columns (status, method, type) must always be their OWN dimension table - never leave them in the fact table
- Examples of columns that must be their own dim: OrderStatus, PaymentMethod, ShippingMethod, ReturnReason

FACT TABLE RULES:
- Only measurements/metrics and foreign keys belong in the fact table
- Measurements include: amounts, costs, quantities, counts, durations, percentages
- Boolean/flag columns must be INT (1/0) never VARCHAR e.g. IsReturned INT
- Prices and rates (e.g. UnitPrice, DiscountPercent) belong in the FACT table not dimensions
- Every fact table must have a DateKey INT FK referencing Dim_Date

ALWAYS CREATE Dim_Date with this exact structure:
CREATE TABLE Dim_Date (
    DateKey INT PRIMARY KEY,
    FullDate DATE NOT NULL,
    DayName VARCHAR(10) NOT NULL,
    DayOfWeek INT NOT NULL,
    DayOfMonth INT NOT NULL,
    WeekOfYear INT NOT NULL,
    MonthNumber INT NOT NULL,
    MonthName VARCHAR(10) NOT NULL,
    Quarter INT NOT NULL,
    Year INT NOT NULL,
    IsWeekend INT NOT NULL
);

OUTPUT RULES:
- Return ONLY valid SQL Server CREATE TABLE statements
- Create all dimension tables first, fact table last
- Always include FOREIGN KEY constraints in the fact table
- Use appropriate SQL Server data types (VARCHAR, INT, DECIMAL(10,2), DATE, BIT)
- Add a comment above each table explaining what it represents"""
            },
            {
                "role": "user",
                "content": f"Reference context from database design books:\n{rag_context}\n\nFlat file columns to analyse:\n{column_summary}\n\nGenerate the star schema SQL CREATE TABLE scripts."
            }
        ],
        max_tokens=2000
    )
    return response.choices[0].message.content

# ------------------------------
# Validate & Compare Schemas via Nemotron
# ------------------------------
def validate_schemas(openrouter_client, schema1: str, schema2: str) -> str:
    response = openrouter_client.chat.completions.create(
        model="nvidia/nemotron-super-49b-v1",
        messages=[
            {
                "role": "system",
                "content": """You are a senior database architect evaluating star schema designs.

Evaluate based on:
- Proper dimension vs fact table separation
- Surrogate keys vs natural keys
- Low cardinality columns in their own dimensions
- Foreign key relationships
- Data type appropriateness
- Normalisation and denormalisation balance

Provide a clear recommendation with specific reasons, highlighting strengths and weaknesses of each schema."""
            },
            {
                "role": "user",
                "content": f"""Compare these two schemas:

SCHEMA 1:
{schema1}

SCHEMA 2:
{schema2}

Which schema is better and why? Be specific about the strengths and weaknesses of each."""
            }
        ],
        max_tokens=1500
    )
    return response.choices[0].message.content

# ------------------------------
# DB Design Assistant
# ------------------------------
def ask_assistant(openai_client, question: str, rag_context: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a database design expert. Answer the question using only the provided context from the reference books. If the answer is not in the context, say so."
            },
            {
                "role": "user",
                "content": f"Context:\n{rag_context}\n\nQuestion: {question}"
            }
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

# ------------------------------
# Streamlit UI
# ------------------------------
st.title("📊 Star Schema Generator")
st.caption("Upload a flat file → get fact & dimension table SQL scripts")

qdrant, openai_client, openrouter_client = load_clients()

tab1, tab2, tab3 = st.tabs(["⚙️ Schema Generator", "✅ Schema Validator", "🔍 DB Design Assistant"])

# ------------------------------
# Tab 1 - Schema Generator
# ------------------------------
with tab1:
    uploaded_file = st.file_uploader("Upload your flat file", type=["csv", "xlsx", "json"])

    if uploaded_file:
        df = load_file(uploaded_file)
        st.success(f"Loaded {len(df)} rows and {len(df.columns)} columns")
        st.dataframe(df.head(5))

        if st.button("Generate Star Schema SQL"):
            with st.spinner("Analysing columns and generating SQL..."):
                column_summary = build_column_summary(df)
                points         = hybrid_search(qdrant, column_summary)
                rag_context    = build_context(points)
                sql            = generate_sql(openai_client, column_summary, rag_context)

            st.markdown("### Generated SQL")
            st.code(sql, language="sql")

            st.download_button(
                label="⬇️ Download SQL file",
                data=sql,
                file_name="star_schema.sql",
                mime="text/plain"
            )

# ------------------------------
# Tab 2 - Schema Validator
# ------------------------------
with tab2:
    st.subheader("Compare Two Schemas")
    st.caption("Paste two SQL schemas and get an expert evaluation from Nemotron")

    col1, col2 = st.columns(2)

    with col1:
        schema1 = st.text_area("Schema 1", height=300, key="schema1")

    with col2:
        schema2 = st.text_area("Schema 2", height=300, key="schema2")

    if st.button("Validate & Compare"):
        if schema1.strip() and schema2.strip():
            with st.spinner("Nemotron analysing schemas..."):
                validation_result = validate_schemas(openrouter_client, schema1, schema2)

            st.markdown("### Evaluation Result")
            st.write(validation_result)
        else:
            st.error("Please paste both schemas to compare")

# ------------------------------
# Tab 3 - DB Design Assistant
# ------------------------------
with tab3:
    st.caption("Ask anything about database design — powered by your reference books")
    question = st.text_input("Ask a question:")

    if question:
        with st.spinner("Searching..."):
            points      = hybrid_search(qdrant, question)
            rag_context = build_context(points)
            answer      = ask_assistant(openai_client, question, rag_context)

        st.markdown("### Answer")
        st.write(answer)

        with st.expander("View source chunks"):
            for i, point in enumerate(points, 1):
                st.markdown(f"**Chunk {i}** | Source: `{point.payload.get('source_file')}` | Page: `{point.payload.get('page_number')}` | Score: `{point.score:.4f}`")
                st.write(point.payload.get('page_content'))
                st.divider()
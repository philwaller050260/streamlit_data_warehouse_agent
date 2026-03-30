import streamlit as st
from qdrant_client import QdrantClient, models as qdrant_models
from openai import OpenAI
import requests
import pandas as pd
import pymssql
import pdfplumber
import io

# ------------------------------
# Config
# ------------------------------
COLLECTION_NAME = "db-design-bge-large"
TOP_K           = 5
HF_API_URL      = "https://router.huggingface.co/hf-inference/models/BAAI/bge-large-en-v1.5/pipeline/feature-extraction"

OPENROUTER_MODELS = {
    "GPT-4o (OpenAI)": "openai/gpt-4o",
}

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
# Azure SQL Connection
# ------------------------------
def get_sql_connection():
    conn = pymssql.connect(
        server=st.secrets["azure_sql_server"],
        user=st.secrets["azure_sql_username"],
        password=st.secrets["azure_sql_password"],
        database=st.secrets["azure_sql_database"],
        tds_version="7.4"
    )
    conn.autocommit(True)
    return conn

# ------------------------------
# Deploy Schema to Azure SQL
# ------------------------------
def deploy_schema(sql: str) -> list:
    sql      = sql.replace("```sql", "").replace("```", "").strip()
    conn     = get_sql_connection()
    cursor   = conn.cursor()
    results  = []

    lines      = [line for line in sql.split("\n") if not line.strip().startswith("--")]
    clean_sql  = "\n".join(lines)
    statements = [s.strip() for s in clean_sql.split(";") if s.strip()]

    for stmt in statements:
        try:
            cursor.execute(stmt)
            results.append({"statement": stmt[:80], "status": "✅ Success"})
        except Exception as e:
            results.append({"statement": stmt[:80], "status": f"❌ Error: {str(e)}"})

    cursor.close()
    conn.close()
    return results

# ------------------------------
# Load uploaded file
# Returns (text, mode) where mode is 'tabular' or 'document'
# ------------------------------
def load_file(uploaded_file) -> tuple:
    name = uploaded_file.name.lower()

    if name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        return df, 'tabular'

    elif name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
        return df, 'tabular'

    elif name.endswith('.json'):
        df = pd.read_json(uploaded_file)
        return df, 'tabular'

    elif name.endswith('.pdf'):
        text = ""
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text, 'document'

    elif name.endswith('.txt') or name.endswith('.md'):
        text = uploaded_file.read().decode('utf-8')
        return text, 'document'

    else:
        raise ValueError(f"Unsupported file type: {uploaded_file.name}")

# ------------------------------
# Build column summary for tabular files
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
# Generate SQL from tabular file
# ------------------------------
def generate_sql_from_columns(openai_client, column_summary: str, rag_context: str) -> str:
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
- Always add these three columns to every dimension table for SCD Type 2 support:
  StartDate DATE NOT NULL DEFAULT GETDATE()
  EndDate DATE NULL
  IsActive BIT NOT NULL DEFAULT 1

FACT TABLE RULES:
- Only measurements/metrics and foreign keys belong in the fact table
- Measurements include: amounts, costs, quantities, counts, durations, percentages
- Boolean/flag columns must be INT (1/0) never VARCHAR e.g. IsReturned INT
- Prices and rates (e.g. UnitPrice, DiscountPercent) belong in the FACT table not dimensions
- Every fact table must have a DateKey INT FK referencing Dim_Date
- Always add CreatedDate DATETIME NOT NULL DEFAULT GETDATE() to every fact table for audit tracking

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
- Use appropriate SQL Server data types (VARCHAR, INT, DECIMAL(10,2), DATE, BIT, DATETIME)
- Add a comment above each table explaining what it represents
- Never include markdown fences or backticks in the output"""
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
# Generate SQL from business requirements document
# ------------------------------
def generate_sql_from_document(openai_client, document_text: str, rag_context: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a senior database architect specialising in star schema design for data warehouses.

Your job is to analyse a business requirements document and generate SQL Server CREATE TABLE scripts following strict star schema best practices.

Read the document carefully and identify:
- What business processes or events need to be measured (these become fact tables)
- What descriptive entities are referenced (these become dimension tables)
- What metrics, amounts, quantities or KPIs are mentioned (these become measures in the fact table)

DIMENSION RULES:
- Descriptive attributes (names, categories, types, statuses, methods) always go in dimension tables
- Every dimension table must have a surrogate key (INT IDENTITY(1,1) PRIMARY KEY) e.g. CustomerKey
- Keep the natural/business key as a separate column e.g. CustomerID
- Low cardinality columns (status, method, type) must always be their OWN dimension table
- Always add these three columns to every dimension table for SCD Type 2 support:
  StartDate DATE NOT NULL DEFAULT GETDATE()
  EndDate DATE NULL
  IsActive BIT NOT NULL DEFAULT 1

FACT TABLE RULES:
- Only measurements/metrics and foreign keys belong in the fact table
- Measurements include: amounts, costs, quantities, counts, durations, percentages
- Boolean/flag columns must be INT (1/0) never VARCHAR
- Every fact table must have a DateKey INT FK referencing Dim_Date
- Always add CreatedDate DATETIME NOT NULL DEFAULT GETDATE() to every fact table for audit tracking

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
- Use appropriate SQL Server data types (VARCHAR, INT, DECIMAL(10,2), DATE, BIT, DATETIME)
- Add a comment above each table explaining what it represents
- Never include markdown fences or backticks in the output"""
            },
            {
                "role": "user",
                "content": f"Reference context from database design books:\n{rag_context}\n\nBusiness requirements document:\n{document_text}\n\nGenerate the star schema SQL CREATE TABLE scripts."
            }
        ],
        max_tokens=2000
    )
    return response.choices[0].message.content

# ------------------------------
# Validate & Compare Schemas
# ------------------------------
def validate_schemas(openrouter_client, schema1: str, schema2: str, model_id: str) -> str:
    response = openrouter_client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": """You are a senior database architect evaluating star schema designs.

Evaluate based on:
- Proper dimension vs fact table separation
- Surrogate keys vs natural keys
- Low cardinality columns in their own dimensions
- Foreign key relationships and correctness
- Data type appropriateness
- Normalisation and denormalisation balance
- Every dimension table must have StartDate, EndDate and IsActive columns for SCD Type 2 support
- Every fact table must have CreatedDate DATETIME NOT NULL DEFAULT GETDATE() for audit tracking
- No markdown fences or backticks in any SQL output

Your response must have TWO sections:

EVALUATION:
Your analysis of both schemas, which is better and why.

CORRECTED SQL:
The best schema with all issues fixed, ready to deploy. Return only valid SQL Server CREATE TABLE statements with no markdown fences, no comments, dimensions first, fact table last."""
            },
            {
                "role": "user",
                "content": f"""Compare these two schemas:

SCHEMA 1:
{schema1}

SCHEMA 2:
{schema2}

Evaluate both and return the corrected best schema."""
            }
        ],
        max_tokens=2000
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
st.caption("Upload a flat file or business requirements document → get fact & dimension table SQL scripts")

qdrant, openai_client, openrouter_client = load_clients()

tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Schema Generator", "✅ Schema Validator", "🔍 DB Design Assistant", "🚀 Deploy Schema"])

# ------------------------------
# Tab 1 - Schema Generator
# ------------------------------
with tab1:
    uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx", "json", "pdf", "txt", "md"])

    if uploaded_file:
        data, mode = load_file(uploaded_file)

        if mode == 'tabular':
            st.success(f"Loaded {len(data)} rows and {len(data.columns)} columns")
            st.dataframe(data.head(5))
        else:
            st.success(f"Loaded document: {uploaded_file.name}")
            with st.expander("Preview document text"):
                st.text(data[:2000] + ("..." if len(data) > 2000 else ""))

        if st.button("Generate Star Schema SQL"):
            with st.spinner("Analysing and generating SQL..."):
                if mode == 'tabular':
                    input_summary = build_column_summary(data)
                    points        = hybrid_search(qdrant, input_summary)
                    rag_context   = build_context(points)
                    sql           = generate_sql_from_columns(openai_client, input_summary, rag_context)
                else:
                    points      = hybrid_search(qdrant, data[:1000])
                    rag_context = build_context(points)
                    sql         = generate_sql_from_document(openai_client, data, rag_context)

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
    st.caption("Paste two SQL schemas and get an expert evaluation")

    selected_label = st.selectbox("Select Evaluator Model", list(OPENROUTER_MODELS.keys()))
    custom_model   = st.text_input("Or paste a custom model ID from OpenRouter (overrides dropdown):")
    model_id       = custom_model.strip() if custom_model.strip() else OPENROUTER_MODELS[selected_label]
    st.caption(f"Using model: `{model_id}`")

    col1, col2 = st.columns(2)

    with col1:
        schema1 = st.text_area("Schema 1", height=300, key="schema1")

    with col2:
        schema2 = st.text_area("Schema 2", height=300, key="schema2")

    if st.button("Validate & Compare"):
        if schema1.strip() and schema2.strip():
            with st.spinner(f"Analysing schemas with {model_id}..."):
                validation_result = validate_schemas(openrouter_client, schema1, schema2, model_id)

            if "CORRECTED SQL:" in validation_result:
                parts      = validation_result.split("CORRECTED SQL:")
                evaluation = parts[0].replace("EVALUATION:", "").strip()
                corrected  = parts[1].strip()

                st.markdown("### Evaluation")
                st.write(evaluation)

                st.markdown("### Corrected SQL — copy into Deploy tab")
                st.code(corrected, language="sql")
            else:
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

# ------------------------------
# Tab 4 - Deploy Schema
# ------------------------------
with tab4:
    st.subheader("Deploy Schema to Azure SQL")
    st.caption("Paste your corrected schema and deploy directly to Azure SQL Server")

    try:
        st.info(f"Target: `{st.secrets['azure_sql_server']}` → `{st.secrets['azure_sql_database']}`")
    except KeyError:
        st.warning("Azure SQL secrets not configured — add them in Streamlit Cloud settings")

    deploy_sql = st.text_area("Paste SQL schema to deploy:", height=400, key="deploy_sql")

    if st.button("🚀 Deploy to Azure SQL", type="primary"):
        if deploy_sql.strip():
            with st.spinner("Deploying to Azure SQL..."):
                try:
                    results = deploy_schema(deploy_sql)
                    st.markdown("### Deployment Results")
                    for r in results:
                        st.write(f"{r['status']} — `{r['statement']}...`")
                    st.success("Deployment complete!")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")
        else:
            st.error("Please paste a SQL schema to deploy")
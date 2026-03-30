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
    "GPT-4o (OpenAI)":   "openai/gpt-4o",
    "GPT-5.1 (OpenAI)":  "openai/gpt-5.1",
    "GPT-5.2 (OpenAI)":  "openai/gpt-5.2",
    "GPT-5.4 (OpenAI)":  "openai/gpt-5.4",
    "Llama 3.3 70B":     "meta-llama/llama-3.3-70b-instruct:free",
}

OPENAI_MODELS = {
    "GPT-4o":          "gpt-4o",
    "GPT-5.1":         "gpt-5.1",
    "GPT-5.2":         "gpt-5.2",
    "GPT-5.4":         "gpt-5.4",
    "GPT-5.4 Mini":    "gpt-5.4-mini",
    "GPT-5.4 Nano":    "gpt-5.4-nano",
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
def generate_sql_from_columns(openai_client, column_summary: str, rag_context: str, model_id: str = "openai/gpt-4o") -> str:
    response = openai_client.chat.completions.create(
        model=model_id,
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
        max_completion_tokens=2000
    )
    return response.choices[0].message.content

# ------------------------------
# Generate SQL from business requirements document
# ------------------------------
def generate_sql_from_document(openai_client, document_text: str, rag_context: str, model_id: str = "openai/gpt-4o") -> str:
    response = openai_client.chat.completions.create(
        model=model_id,
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
        max_completion_tokens=2000
    )
    return response.choices[0].message.content

# ------------------------------
# Validate & Compare Schemas
# ------------------------------
def validate_schemas(openrouter_client, schema1: str, schema2: str, model_id: str) -> str:
    try:
        response = openrouter_client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior database architect evaluating star schema designs.\n\n"
                        "Evaluate based on:\n"
                        "- Proper dimension vs fact table separation\n"
                        "- Surrogate keys vs natural keys\n"
                        "- Low cardinality columns in their own dimensions\n"
                        "- Foreign key relationships and correctness\n"
                        "- Data type appropriateness\n"
                        "- Normalisation and denormalisation balance\n"
                        "- Every dimension table must have StartDate, EndDate and IsActive columns for SCD Type 2 support\n"
                        "- Every fact table must have CreatedDate DATETIME NOT NULL DEFAULT GETDATE() for audit tracking\n"
                        "- No markdown fences or backticks in any SQL output\n"
                        "- Check whether any dimension could appear more than once in a transaction with different roles — if so, the fact table must have separate foreign keys for each role e.g. PickupBranchKey and ReturnBranchKey\n\n"
                        "Your response must have TWO sections:\n\n"
                        "EVALUATION:\n"
                        "Your analysis of both schemas, which is better and why.\n\n"
                        "CORRECTED SQL:\n"
                        "The best schema with all issues fixed, ready to deploy. Return only valid SQL Server CREATE TABLE statements with no markdown fences, no comments, dimensions first, fact table last."
                    )
                },
                {
                    "role": "user",
                    "content": "Compare these two schemas:\n\nSCHEMA 1:\n" + schema1 + "\n\nSCHEMA 2:\n" + schema2 + "\n\nEvaluate both and return the corrected best schema."
                }
            ],
            max_completion_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return "EVALUATION:\nAPI Error: " + str(e) + "\n\nCORRECTED SQL:\n-- No output due to error"

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
        max_completion_tokens=1000
    )
    return response.choices[0].message.content


# ------------------------------
# Generate DBML from SQL
# ------------------------------
def generate_dbml(client, sql: str, model_id: str) -> str:
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a database architect. Convert the SQL Server CREATE TABLE statements provided into DBML format compatible with dbdiagram.io.\n\n"
                        "Rules:\n"
                        "- Use Table keyword for each table\n"
                        "- Use [pk, increment] for IDENTITY primary keys\n"
                        "- Use [ref: > TableName.ColumnName] for foreign keys\n"
                        "- Use correct DBML data types: int, varchar, decimal, date, datetime, bit\n"
                        "- Output ONLY valid DBML, no explanation, no markdown fences"
                    )
                },
                {
                    "role": "user",
                    "content": "Convert this SQL to DBML:\n\n" + sql
                }
            ],
            max_completion_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Error generating DBML: " + str(e)

# ------------------------------
# Naming Convention Check
# ------------------------------
def check_naming_conventions(client, sql: str, model_id: str) -> str:
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a database architect performing a naming convention sanity check on a star schema.\n\n"
                        "Check for the following issues and report each one clearly:\n"
                        "- Dimension tables must be prefixed with Dim_ (e.g. Dim_Customer)\n"
                        "- Fact tables must be prefixed with Fact_ (e.g. Fact_Sales)\n"
                        "- Surrogate keys must be suffixed with Key (e.g. CustomerKey)\n"
                        "- Natural/business keys should be suffixed with ID (e.g. CustomerID)\n"
                        "- No spaces or special characters in column or table names\n"
                        "- Boolean columns should start with Is or Has (e.g. IsActive, HasDiscount)\n"
                        "- Date foreign keys should be suffixed with DateKey (e.g. OrderDateKey)\n"
                        "- No ambiguous column names like Name, Type, Status without a prefix\n\n"
                        "Format your response as:\n"
                        "PASSED:\n"
                        "- list of things that look correct\n\n"
                        "ISSUES:\n"
                        "- list of specific issues found with table and column name\n\n"
                        "SUGGESTIONS:\n"
                        "- specific rename suggestions"
                    )
                },
                {
                    "role": "user",
                    "content": "Check this schema:\n\n" + sql
                }
            ],
            max_completion_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Error checking naming conventions: " + str(e)

# ------------------------------
# Generate Sample INSERT Data
# ------------------------------
def generate_sample_data(client, sql: str, model_id: str) -> str:
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a database architect generating realistic sample INSERT statements for a star schema.\n\n"
                        "Rules:\n"
                        "- Generate 3-5 rows per dimension table\n"
                        "- Generate 5 rows for each fact table\n"
                        "- Use realistic values based on column names and table context\n"
                        "- Do not insert into identity/surrogate key columns\n"
                        "- Insert dimension tables first, fact tables last\n"
                        "- Use correct SQL Server syntax\n"
                        "- Output ONLY valid SQL INSERT statements, no markdown fences, no comments"
                    )
                },
                {
                    "role": "user",
                    "content": "Generate sample INSERT data for this schema:\n\n" + sql
                }
            ],
            max_completion_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Error generating sample data: " + str(e)

# ------------------------------
# Schema Diff vs Azure SQL
# ------------------------------
def get_existing_schema() -> str:
    try:
        conn   = get_sql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                t.TABLE_NAME,
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.CHARACTER_MAXIMUM_LENGTH,
                c.IS_NULLABLE,
                c.COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.TABLES t
            JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
        """)
        rows    = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            return ""

        result  = {}
        for row in rows:
            tbl = row[0]
            if tbl not in result:
                result[tbl] = []
            result[tbl].append(f"  {row[1]} {row[2]}" + (f"({row[3]})" if row[3] else "") + (" NULL" if row[4] == "YES" else " NOT NULL"))

        output = ""
        for tbl, cols in result.items():
            output += f"Table: {tbl}\n" + "\n".join(cols) + "\n\n"
        return output
    except Exception as e:
        return f"Error reading existing schema: {str(e)}"

def generate_schema_diff(client, new_sql: str, existing_schema: str, model_id: str) -> str:
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a database architect comparing a new schema against an existing deployed schema.\n\n"
                        "Analyse both schemas and report:\n\n"
                        "NEW TABLES:\n"
                        "- Tables in the new schema that do not exist in the deployed schema\n\n"
                        "MODIFIED TABLES:\n"
                        "- Tables that exist in both but have column differences (added, removed, changed columns)\n\n"
                        "REMOVED TABLES:\n"
                        "- Tables in the deployed schema that are not in the new schema\n\n"
                        "NO CHANGE:\n"
                        "- Tables that are identical in both schemas\n\n"
                        "Be specific with column names and data types."
                    )
                },
                {
                    "role": "user",
                    "content": "EXISTING DEPLOYED SCHEMA:\n\n" + existing_schema + "\n\nNEW SCHEMA:\n\n" + new_sql
                }
            ],
            max_completion_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Error generating diff: " + str(e)

# ------------------------------
# Streamlit UI
# ------------------------------
st.title("📊 Star Schema Generator")
st.caption("Upload a flat file or business requirements document → get fact & dimension table SQL scripts")

qdrant, openai_client, openrouter_client = load_clients()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["⚙️ Schema Generator", "✅ Schema Validator", "🔍 DB Design Assistant", "🔎 Sanity Check", "📊 Schema Diff", "🚀 Deploy Schema"])

# ------------------------------
# Tab 1 - Schema Generator
# ------------------------------
with tab1:
    uploaded_file  = st.file_uploader("Upload your file", type=["csv", "xlsx", "json", "pdf", "txt", "md"])
    t1_provider    = st.radio("Provider", ["OpenAI", "OpenRouter"], horizontal=True, key="t1_provider")
    if t1_provider == "OpenAI":
        t1_label    = st.selectbox("Select Model", list(OPENAI_MODELS.keys()), key="t1_model_select")
        t1_model_id = OPENAI_MODELS[t1_label]
        t1_client   = openai_client
    else:
        t1_label    = st.selectbox("Select Model", list(OPENROUTER_MODELS.keys()), key="t1_model_select_or")
        t1_custom   = st.text_input("Or paste a custom OpenRouter model ID:", key="t1_custom")
        t1_model_id = t1_custom.strip() if t1_custom.strip() else OPENROUTER_MODELS[t1_label]
        t1_client   = openrouter_client
    st.caption(f"Using model: `{t1_model_id}`")

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
                    sql           = generate_sql_from_columns(t1_client, input_summary, rag_context, t1_model_id)
                else:
                    points      = hybrid_search(qdrant, data[:1000])
                    rag_context = build_context(points)
                    sql         = generate_sql_from_document(t1_client, data, rag_context, t1_model_id)

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
    st.caption("Upload two SQL schema files and get an expert evaluation")

    t2_provider = st.radio("Provider", ["OpenAI", "OpenRouter"], horizontal=True, key="t2_provider")
    if t2_provider == "OpenAI":
        t2_label    = st.selectbox("Select Evaluator Model", list(OPENAI_MODELS.keys()), key="t2_model_select")
        model_id    = OPENAI_MODELS[t2_label]
        t2_client   = openai_client
    else:
        t2_label     = st.selectbox("Select Evaluator Model", list(OPENROUTER_MODELS.keys()), key="t2_model_select_or")
        custom_model = st.text_input("Or paste a custom OpenRouter model ID:", key="t2_custom")
        model_id     = custom_model.strip() if custom_model.strip() else OPENROUTER_MODELS[t2_label]
        t2_client    = openrouter_client
    st.caption(f"Using model: `{model_id}`")

    col1, col2 = st.columns(2)

    with col1:
        schema1_file = st.file_uploader("Upload Schema 1 (.sql)", type=["sql", "txt"], key="schema1_file")
        schema1      = schema1_file.read().decode("utf-8") if schema1_file else ""
        if schema1:
            st.code(schema1[:500] + ("..." if len(schema1) > 500 else ""), language="sql")

    with col2:
        schema2_file = st.file_uploader("Upload Schema 2 (.sql)", type=["sql", "txt"], key="schema2_file")
        schema2      = schema2_file.read().decode("utf-8") if schema2_file else ""
        if schema2:
            st.code(schema2[:500] + ("..." if len(schema2) > 500 else ""), language="sql")

    if st.button("Validate & Compare"):
        if schema1.strip() and schema2.strip():
            with st.spinner(f"Analysing schemas with {model_id}..."):
                validation_result = validate_schemas(t2_client, schema1, schema2, model_id)

            validation_result = validation_result or ""

            if "API Error" in validation_result:
                st.error(validation_result)
            elif "CORRECTED SQL:" in validation_result:
                parts      = validation_result.split("CORRECTED SQL:")
                evaluation = parts[0].replace("EVALUATION:", "").strip()
                corrected  = parts[1].strip()

                st.markdown("### Evaluation")
                st.write(evaluation)

                st.markdown("### Corrected SQL")
                st.code(corrected, language="sql")
                st.download_button(
                    label="⬇️ Download Corrected SQL",
                    data=corrected,
                    file_name="corrected_schema.sql",
                    mime="text/plain"
                )
            else:
                st.warning("Model did not follow expected format. Raw output:")
                st.code(validation_result)
        else:
            st.error("Please upload both schema files to compare")

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
# Tab 4 - Sanity Check
# ------------------------------
with tab4:
    st.subheader("🔎 Sanity Check")
    st.caption("Generate DBML for dbdiagram.io, check naming conventions, and generate sample data")

    t4_provider = st.radio("Provider", ["OpenAI", "OpenRouter"], horizontal=True, key="t4_provider")
    if t4_provider == "OpenAI":
        t4_label    = st.selectbox("Select Model", list(OPENAI_MODELS.keys()), key="t4_model_select")
        t4_model_id = OPENAI_MODELS[t4_label]
        t4_client   = openai_client
    else:
        t4_label    = st.selectbox("Select Model", list(OPENROUTER_MODELS.keys()), key="t4_model_select_or")
        t4_custom   = st.text_input("Or paste a custom OpenRouter model ID:", key="t4_custom")
        t4_model_id = t4_custom.strip() if t4_custom.strip() else OPENROUTER_MODELS[t4_label]
        t4_client   = openrouter_client
    st.caption(f"Using model: `{t4_model_id}`")

    t4_file = st.file_uploader("Upload SQL schema (.sql)", type=["sql", "txt"], key="t4_file")
    t4_sql  = t4_file.read().decode("utf-8") if t4_file else ""

    if t4_sql:
        with st.expander("Preview SQL"):
            st.code(t4_sql[:500] + ("..." if len(t4_sql) > 500 else ""), language="sql")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("Generate DBML"):
            if t4_sql.strip():
                with st.spinner("Generating DBML..."):
                    dbml = generate_dbml(t4_client, t4_sql, t4_model_id)
                st.markdown("### DBML — paste into dbdiagram.io")
                st.code(dbml, language="text")
                st.download_button("⬇️ Download DBML", data=dbml, file_name="schema.dbml", mime="text/plain")
            else:
                st.error("Please upload a SQL schema file")

    with col_b:
        if st.button("Check Naming Conventions"):
            if t4_sql.strip():
                with st.spinner("Checking naming conventions..."):
                    convention_result = check_naming_conventions(t4_client, t4_sql, t4_model_id)
                st.markdown("### Naming Convention Report")
                st.write(convention_result)
            else:
                st.error("Please upload a SQL schema file")

    with col_c:
        if st.button("Generate Sample Data"):
            if t4_sql.strip():
                with st.spinner("Generating sample INSERT statements..."):
                    sample_data = generate_sample_data(t4_client, t4_sql, t4_model_id)
                st.markdown("### Sample INSERT Statements")
                st.code(sample_data, language="sql")
                st.download_button("⬇️ Download Sample Data", data=sample_data, file_name="sample_data.sql", mime="text/plain")
            else:
                st.error("Please upload a SQL schema file")

# ------------------------------
# Tab 5 - Schema Diff
# ------------------------------
with tab5:
    st.subheader("📊 Schema Diff")
    st.caption("Compare your new schema against what is already deployed in Azure SQL")

    t5_provider = st.radio("Provider", ["OpenAI", "OpenRouter"], horizontal=True, key="t5_provider")
    if t5_provider == "OpenAI":
        t5_label    = st.selectbox("Select Model", list(OPENAI_MODELS.keys()), key="t5_model_select")
        t5_model_id = OPENAI_MODELS[t5_label]
        t5_client   = openai_client
    else:
        t5_label    = st.selectbox("Select Model", list(OPENROUTER_MODELS.keys()), key="t5_model_select_or")
        t5_custom   = st.text_input("Or paste a custom OpenRouter model ID:", key="t5_custom")
        t5_model_id = t5_custom.strip() if t5_custom.strip() else OPENROUTER_MODELS[t5_label]
        t5_client   = openrouter_client
    st.caption(f"Using model: `{t5_model_id}`")

    try:
        st.info(f"Target: `{st.secrets['azure_sql_server']}` → `{st.secrets['azure_sql_database']}`")
    except KeyError:
        st.warning("Azure SQL secrets not configured")

    t5_file = st.file_uploader("Upload new SQL schema (.sql)", type=["sql", "txt"], key="t5_file")
    t5_sql  = t5_file.read().decode("utf-8") if t5_file else ""

    if t5_sql:
        with st.expander("Preview new schema"):
            st.code(t5_sql[:500] + ("..." if len(t5_sql) > 500 else ""), language="sql")

    if st.button("Run Schema Diff"):
        if t5_sql.strip():
            with st.spinner("Reading existing schema from Azure SQL..."):
                existing = get_existing_schema()
            if existing.startswith("Error"):
                st.error(existing)
            elif not existing:
                st.warning("No existing tables found in the database — looks like a fresh deployment.")
            else:
                with st.expander("View existing deployed schema"):
                    st.text(existing)
                with st.spinner("Comparing schemas..."):
                    diff_result = generate_schema_diff(t5_client, t5_sql, existing, t5_model_id)
                st.markdown("### Schema Diff Report")
                st.write(diff_result)
        else:
            st.error("Please upload a SQL schema file")

# ------------------------------
# Tab 6 - Deploy Schema
# ------------------------------
with tab6:
    st.subheader("Deploy Schema to Azure SQL")
    st.caption("Upload a .sql file and deploy directly to Azure SQL Server")

    try:
        st.info(f"Target: `{st.secrets['azure_sql_server']}` → `{st.secrets['azure_sql_database']}`")
    except KeyError:
        st.warning("Azure SQL secrets not configured — add them in Streamlit Cloud settings")

    deploy_file = st.file_uploader("Upload SQL schema to deploy (.sql)", type=["sql", "txt"], key="deploy_file")
    deploy_sql  = deploy_file.read().decode("utf-8") if deploy_file else ""

    if deploy_sql:
        with st.expander("Preview SQL"):
            st.code(deploy_sql[:500] + ("..." if len(deploy_sql) > 500 else ""), language="sql")

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
            st.error("Please upload a SQL schema file to deploy")
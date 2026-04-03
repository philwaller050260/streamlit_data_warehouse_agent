import streamlit as st
from openai import OpenAI
import pymssql

# Config
OPENROUTER_MODELS = {
    "GPT-4o (OpenAI)":   "openai/gpt-4o",
    "GPT-5.1 (OpenAI)":  "openai/gpt-5.1",
    "GPT-5.2 (OpenAI)":  "openai/gpt-5.2",
    "GPT-5.4 (OpenAI)":  "openai/gpt-5.4",
    "Llama 3.3 70B":     "meta-llama/llama-3.3-70b-instruct:free",
}

OPENAI_MODELS = {
    "GPT-4o":          "gpt-4o",
    "gpt-4o-mini":     "gpt-4o-mini",
    "GPT-5.1":         "gpt-5.1",
    "GPT-5.2":         "gpt-5.2",
    "GPT-5.4":         "gpt-5.4",
    "GPT-5.4 Mini":    "gpt-5.4-mini",
    "GPT-5.4 Nano":    "gpt-5.4-nano",
    
}

# Clients
@st.cache_resource
def load_clients():
    openai_client = OpenAI(api_key=st.secrets["openai_api_key"])
    openrouter_client = OpenAI(
        api_key=st.secrets["openrouter_api_key"],
        base_url="https://openrouter.ai/api/v1"
    )
    return openai_client, openrouter_client

# Azure SQL Connection
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

# Deploy schema to Azure SQL
def deploy_schema(sql: str) -> list:
    sql = sql.replace("```sql", "").replace("```", "").strip()
    conn = get_sql_connection()
    cursor = conn.cursor()
    results = []

    lines = [line for line in sql.split("\n") if not line.strip().startswith("--")]
    clean_sql = "\n".join(lines)
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

# Get existing schema from Azure SQL
def get_existing_schema() -> str:
    try:
        conn = get_sql_connection()
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
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            return ""

        result = {}
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

# Generate SQL from logical model
def generate_sql_from_logical_model(client, logical_model: str, model_id: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": """You are a senior database architect. Convert a logical data model into SQL Server CREATE TABLE statements.

Your job is to translate the logical model (entities, foreign keys, attributes, SCD types) into production-ready SQL.

RULES:
- Create DIMENSION tables first, FACT tables last
- Every dimension surrogate key is INT IDENTITY(1,1) PRIMARY KEY
- Every dimension must include: StartDate DATE, EndDate DATE NULL, IsActive BIT
- Every dimension must include: natural/business key column (e.g., CustomerID)
- Every fact table must have a surrogate INT IDENTITY(1,1) PRIMARY KEY
- Every fact table must have CreatedDate DATETIME NOT NULL DEFAULT GETDATE()
- All foreign keys must be INT and reference the surrogate key
- Use DECIMAL(10,2) for amounts/prices, INT for quantities
- Use VARCHAR(255) for text, DATE for dates, BIT for booleans
- Add CHECK constraints for BIT columns (0 or 1)
- Add appropriate indexes on foreign keys

DATA TYPES:
- Surrogate keys: INT IDENTITY(1,1) PRIMARY KEY
- Natural keys: VARCHAR(50) NOT NULL UNIQUE
- Names/text: VARCHAR(255)
- Amounts: DECIMAL(10,2)
- Quantities: INT
- Dates: DATE
- Booleans: BIT (0/1)
- Timestamps: DATETIME NOT NULL DEFAULT GETDATE()

SCD IMPLEMENTATION:
- Type 1: UPDATE existing row (no StartDate/EndDate needed)
- Type 2: Keep history - add StartDate, EndDate, IsActive
- Type 3: Keep limited history - add previous value columns

ROLE-PLAYING DIMENSIONS:
If a dimension has multiple roles (e.g., Branch as PickupBranch and ReturnBranch):
- Create separate tables: Dim_BranchPickup, Dim_BranchReturn
- Identical structure, different names
- Fact table has separate FKs: PickupBranchKey, ReturnBranchKey

OUTPUT:
- Return ONLY valid SQL Server CREATE TABLE statements
- No markdown fences, no comments
- Dimensions first, fact tables last
- Include FOREIGN KEY constraints in fact tables"""
            },
            {
                "role": "user",
                "content": f"Logical model to convert to SQL:\n\n{logical_model}"
            }
        ],
        max_completion_tokens=2500
    )
    return response.choices[0].message.content

# Generate DBML from SQL
def generate_dbml(client, sql: str, model_id: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": """Convert SQL Server CREATE TABLE statements to DBML format for dbdiagram.io.

Rules:
- Use Table keyword for each table
- Use [pk, increment] for IDENTITY primary keys
- Use [ref: > TableName.ColumnName] for foreign keys
- Use correct DBML data types: int, varchar, decimal, date, datetime, bit
- Output ONLY valid DBML, no explanation, no markdown fences"""
            },
            {
                "role": "user",
                "content": f"Convert to DBML:\n\n{sql}"
            }
        ],
        max_completion_tokens=2000
    )
    return response.choices[0].message.content

# Generate sample INSERT data
def generate_sample_data(client, sql: str, model_id: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": """Generate realistic sample INSERT statements for a star schema.

Rules:
- Generate 3-5 rows per dimension table
- Generate 5 rows per fact table
- Use realistic business values
- Do NOT insert into IDENTITY columns (let SQL Server generate them)
- Insert dimensions FIRST, facts LAST
- Use correct SQL Server syntax
- Output ONLY valid INSERT statements, no markdown fences, no comments"""
            },
            {
                "role": "user",
                "content": f"Generate sample data for:\n\n{sql}"
            }
        ],
        max_completion_tokens=2000
    )
    return response.choices[0].message.content

# Check naming conventions
def check_naming_conventions(client, sql: str, model_id: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": """Review SQL schema naming conventions.

Check for:
- Dimension tables prefixed with Dim_
- Fact tables prefixed with Fact_
- Surrogate keys suffixed with Key
- Natural keys suffixed with ID
- No spaces/special characters
- Boolean columns start with Is/Has
- Date FKs suffixed with DateKey

Format response as:
PASSED:
- list of correct naming

ISSUES:
- specific problems found

SUGGESTIONS:
- rename recommendations"""
            },
            {
                "role": "user",
                "content": f"Check naming:\n\n{sql}"
            }
        ],
        max_completion_tokens=1500
    )
    return response.choices[0].message.content

# Main UI
st.title("⚙️ Schema Generator")
st.caption("Convert logical model into SQL CREATE TABLE statements")

openai_client, openrouter_client = load_clients()

# Provider selection
col1, col2 = st.columns([2, 3])
with col1:
    provider = st.radio("Provider", ["OpenAI", "OpenRouter"], horizontal=True)
with col2:
    if provider == "OpenAI":
        model_label = st.selectbox("Select Model", list(OPENAI_MODELS.keys()))
        model_id = OPENAI_MODELS[model_label]
        client = openai_client
    else:
        model_label = st.selectbox("Select Model", list(OPENROUTER_MODELS.keys()))
        custom = st.text_input("Or paste custom OpenRouter model ID:")
        model_id = custom.strip() if custom.strip() else OPENROUTER_MODELS[model_label]
        client = openrouter_client

st.caption(f"Using: `{model_id}`")
st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 Generate SQL", "🔎 Sanity Check", "📊 Schema Diff", "🚀 Deploy", "DBML", "Sample Data"])

# Tab 1 - Generate SQL
with tab1:
    st.subheader("Generate SQL from Logical Model")
    
    input_method = st.radio("Input method", ["Upload file", "Paste text"], horizontal=True, key="gen_input")
    
    logical_model = ""
    
    if input_method == "Upload file":
        uploaded_file = st.file_uploader("Upload logical model (.txt)", type=["txt"], key="logical_file")
        if uploaded_file:
            logical_model = uploaded_file.read().decode("utf-8")
            with st.expander("Preview"):
                st.text(logical_model[:500] + ("..." if len(logical_model) > 500 else ""))
    else:
        logical_model = st.text_area("Paste logical model:", height=300, key="logical_text")
    
    if st.button("Generate SQL"):
        if logical_model.strip():
            with st.spinner("Generating SQL..."):
                sql = generate_sql_from_logical_model(client, logical_model, model_id)
            
            st.markdown("### Generated SQL")
            st.code(sql, language="sql")
            
            st.download_button("⬇️ Download SQL", data=sql, file_name="schema.sql", mime="text/plain")
        else:
            st.error("Please provide a logical model")

# Tab 2 - Sanity Check
with tab2:
    st.subheader("🔎 Sanity Check")
    
    sql_file = st.file_uploader("Upload SQL schema (.sql)", type=["sql", "txt"], key="check_file")
    sql = sql_file.read().decode("utf-8") if sql_file else ""
    
    if sql:
        with st.expander("Preview"):
            st.code(sql[:500] + ("..." if len(sql) > 500 else ""), language="sql")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Check Naming Conventions"):
            if sql.strip():
                with st.spinner("Checking..."):
                    result = check_naming_conventions(client, sql, model_id)
                st.write(result)
            else:
                st.error("Please upload SQL")
    
    with col2:
        if st.button("Generate DBML"):
            if sql.strip():
                with st.spinner("Generating DBML..."):
                    dbml = generate_dbml(client, sql, model_id)
                st.code(dbml, language="text")
                st.download_button("⬇️ Download DBML", data=dbml, file_name="schema.dbml", mime="text/plain")
            else:
                st.error("Please upload SQL")
    
    with col3:
        if st.button("Generate Sample Data"):
            if sql.strip():
                with st.spinner("Generating sample data..."):
                    samples = generate_sample_data(client, sql, model_id)
                st.code(samples, language="sql")
                st.download_button("⬇️ Download Samples", data=samples, file_name="sample_data.sql", mime="text/plain")
            else:
                st.error("Please upload SQL")

# Tab 3 - Schema Diff
with tab3:
    st.subheader("📊 Schema Diff")
    st.caption("Compare new schema against deployed schema in Azure SQL")
    
    try:
        st.info(f"Target: `{st.secrets['azure_sql_server']}` → `{st.secrets['azure_sql_database']}`")
    except KeyError:
        st.warning("Azure SQL secrets not configured")
    
    diff_file = st.file_uploader("Upload new SQL schema (.sql)", type=["sql", "txt"], key="diff_file")
    diff_sql = diff_file.read().decode("utf-8") if diff_file else ""
    
    if st.button("Run Diff"):
        if diff_sql.strip():
            with st.spinner("Reading existing schema..."):
                existing = get_existing_schema()
            
            if existing.startswith("Error"):
                st.error(existing)
            elif not existing:
                st.info("No existing tables — fresh deployment")
            else:
                with st.expander("View existing schema"):
                    st.text(existing)
                st.success("Compare above with your new schema to identify changes")
        else:
            st.error("Please upload SQL")

# Tab 4 - Deploy
with tab4:
    st.subheader("🚀 Deploy to Azure SQL")
    st.caption("Deploy SQL directly to Azure SQL Server")
    
    try:
        st.info(f"Target: `{st.secrets['azure_sql_server']}` → `{st.secrets['azure_sql_database']}`")
    except KeyError:
        st.error("Azure SQL secrets not configured")
    
    deploy_file = st.file_uploader("Upload SQL to deploy (.sql)", type=["sql", "txt"], key="deploy_file")
    deploy_sql = deploy_file.read().decode("utf-8") if deploy_file else ""
    
    if deploy_sql:
        with st.expander("Preview"):
            st.code(deploy_sql[:500] + ("..." if len(deploy_sql) > 500 else ""), language="sql")
    
    if st.button("🚀 Deploy", type="primary"):
        if deploy_sql.strip():
            with st.spinner("Deploying..."):
                try:
                    results = deploy_schema(deploy_sql)
                    st.markdown("### Results")
                    for r in results:
                        st.write(f"{r['status']} — `{r['statement']}...`")
                    st.success("Deployment complete!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.error("Please upload SQL")

# Tab 5 - DBML
with tab5:
    st.subheader("📐 DBML Visualization")
    st.caption("Paste DBML code, then open dbdiagram.io and paste it there")
    
    dbml_file = st.file_uploader("Upload DBML file (.dbml)", type=["dbml", "txt"], key="dbml_file")
    if dbml_file:
        dbml_text = dbml_file.read().decode("utf-8")
        st.code(dbml_text, language="text")

# Tab 6 - Sample Data
with tab6:
    st.subheader("📊 Sample Data")
    
    sample_file = st.file_uploader("Upload sample data (.sql)", type=["sql", "txt"], key="sample_file")
    if sample_file:
        sample_text = sample_file.read().decode("utf-8")
        st.code(sample_text, language="sql")
import streamlit as st
from openai import OpenAI

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

# Generate DBML from SQL schema
def generate_dbml_from_sql(client, sql: str, model_id: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": """You are a database architect. Convert SQL Server CREATE TABLE statements into DBML format for dbdiagram.io visualization.

Your job is to parse the SQL and output valid DBML that shows the actual physical schema.

DBML CONVERSION RULES:
- Use 'Table table_name' for each CREATE TABLE
- Use [pk] for PRIMARY KEY columns
- Use [pk, increment] for INT IDENTITY columns
- Use [unique] for UNIQUE constraints
- Use [not null] for NOT NULL columns
- Use [ref: > other_table.column] for FOREIGN KEY relationships
- Use appropriate DBML data types: int, varchar, decimal, date, datetime, bit
- Include comments with // for table and column descriptions

SQL TO DBML DATA TYPE MAPPING:
- INT → int
- VARCHAR(n) → varchar
- DECIMAL(10,2) → decimal
- DATE → date
- DATETIME → datetime
- BIT → bit

FOREIGN KEYS:
- Parse FOREIGN KEY constraints
- Use [ref: > ReferencedTable.column] syntax
- Show all FK relationships clearly

INDEXES:
- Note any indexes with comments

OUTPUT:
- Return ONLY valid DBML code
- No markdown fences, no backticks
- Ready to paste directly into dbdiagram.io
- Include helpful comments explaining the schema
- Show table purposes in comments"""
            },
            {
                "role": "user",
                "content": f"SQL schema to convert to DBML:\n\n{sql}"
            }
        ],
        max_completion_tokens=2500
    )
    return response.choices[0].message.content

# Main UI
st.title("📐 DBML Physical Generator")
st.caption("Convert SQL schema into DBML for visualization on dbdiagram.io")

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

# Input
st.subheader("Input: SQL Schema")
input_method = st.radio("Input method", ["Upload file", "Paste text"], horizontal=True)

sql = ""

if input_method == "Upload file":
    uploaded_file = st.file_uploader("Upload SQL schema (.sql)", type=["sql", "txt"])
    if uploaded_file:
        sql = uploaded_file.read().decode("utf-8")
        with st.expander("Preview"):
            st.code(sql[:500] + ("..." if len(sql) > 500 else ""), language="sql")
else:
    sql = st.text_area("Paste SQL schema:", height=300)

# Generate
if st.button("Generate DBML"):
    if sql.strip():
        with st.spinner("Generating DBML..."):
            dbml = generate_dbml_from_sql(client, sql, model_id)
        
        st.markdown("### Generated DBML")
        st.code(dbml, language="text")
        
        st.info("📋 Copy above and paste into https://dbdiagram.io to visualize")
        
        st.download_button("⬇️ Download DBML", data=dbml, file_name="physical_schema.dbml", mime="text/plain")
    else:
        st.error("Please provide SQL schema")
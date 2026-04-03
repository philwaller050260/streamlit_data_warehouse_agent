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
- Every dimension must include: StartDate DATE, EndDate DATE NULL, IsActive BIT (for SCD Type 2)
- Every dimension must include: natural/business key column (e.g., CustomerID)
- Every fact table must have a surrogate INT IDENTITY(1,1) PRIMARY KEY
- Every fact table must have CreatedDate DATETIME NOT NULL DEFAULT GETDATE()
- All foreign keys must be INT and reference the surrogate key
- Use DECIMAL(10,2) for amounts/prices, INT for quantities
- Use VARCHAR(255) for text, DATE for dates, BIT for booleans
- Add CHECK constraints for BIT columns (0 or 1)

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
- Type 1: No history (just overwrite)
- Type 2: Keep full history - add StartDate, EndDate, IsActive
- Type 3: Keep limited history - add previous value columns

ROLE-PLAYING DIMENSIONS:
If a dimension has multiple roles (e.g., Branch as PickupBranch and ReturnBranch):
- Create separate tables: Dim_BranchPickup, Dim_BranchReturn
- Identical structure, different names
- Fact table has separate FKs: PickupBranchKey, ReturnBranchKey

OUTPUT:
- Return ONLY valid SQL Server CREATE TABLE statements
- No markdown fences, no backticks
- Dimensions first, fact tables last
- Include FOREIGN KEY constraints in fact tables
- No comments"""
            },
            {
                "role": "user",
                "content": f"Logical model to convert to SQL:\n\n{logical_model}"
            }
        ],
        max_completion_tokens=2500
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

# Input
st.subheader("Input: Logical Model")
input_method = st.radio("Input method", ["Upload file", "Paste text"], horizontal=True)

logical_model = ""

if input_method == "Upload file":
    uploaded_file = st.file_uploader("Upload logical model (.txt)", type=["txt"])
    if uploaded_file:
        logical_model = uploaded_file.read().decode("utf-8")
        with st.expander("Preview"):
            st.text(logical_model[:500] + ("..." if len(logical_model) > 500 else ""))
else:
    logical_model = st.text_area("Paste logical model:", height=300)

# Generate
if st.button("Generate SQL"):
    if logical_model.strip():
        with st.spinner("Generating SQL..."):
            sql = generate_sql_from_logical_model(client, logical_model, model_id)
        
        st.markdown("### Generated SQL")
        st.code(sql, language="sql")
        
        st.download_button("⬇️ Download SQL", data=sql, file_name="schema.sql", mime="text/plain")
    else:
        st.error("Please provide a logical model")
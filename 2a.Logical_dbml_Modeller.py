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

# Generate DBML from logical model
def generate_dbml_from_logical_model(client, logical_model: str, model_id: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": """You are a database architect. Convert a logical data model into DBML format for dbdiagram.io visualization.

Your job is to take the logical model description (entities, attributes, relationships, SCD types) and output valid DBML that can be pasted directly into dbdiagram.io.

DBML RULES:
- Use 'Table EntityName' for each entity
- Use [pk, increment] for INT IDENTITY surrogate keys
- Use [unique] for natural/business keys
- Use column_name column_type for each attribute
- Use [ref: > OtherTable.column] for foreign key relationships
- Use [ref: < OtherTable.column] for reverse relationships
- Comment tables and relationships with // or /* */

DATA TYPES IN DBML:
- int for INT columns
- varchar for VARCHAR columns
- decimal for DECIMAL columns
- date for DATE columns
- datetime for DATETIME columns
- bit for BIT columns

DIMENSION TABLES:
- Use Dim_EntityName naming
- Include surrogate key [pk, increment]
- Include natural key [unique]
- For SCD Type 2: include StartDate, EndDate, IsActive columns
- For SCD Type 1: no history columns needed

FACT TABLES:
- Use Fact_EntityName naming
- Include surrogate key [pk, increment]
- Include all foreign keys to dimension tables
- Include all measures/metrics columns
- Include CreatedDate for audit

RELATIONSHIPS:
- Many-to-One (M:1): fact to dimension uses [ref: > Dim_Table.key]
- One-to-Many (1:N): use [ref: < ]
- Role-playing dimensions: create separate table entries with different names

OUTPUT:
- Return ONLY valid DBML code
- No markdown fences, no backticks
- Ready to paste directly into dbdiagram.io
- Include comments explaining the model"""
            },
            {
                "role": "user",
                "content": f"Logical model to convert to DBML:\n\n{logical_model}"
            }
        ],
        max_completion_tokens=2500
    )
    return response.choices[0].message.content

# Main UI
st.title("📐 DBML Logical Generator")
st.caption("Convert logical model into DBML for visualization on dbdiagram.io")

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
if st.button("Generate DBML"):
    if logical_model.strip():
        with st.spinner("Generating DBML..."):
            dbml = generate_dbml_from_logical_model(client, logical_model, model_id)
        
        st.markdown("### Generated DBML")
        st.code(dbml, language="text")
        
        st.info("📋 Copy above and paste into https://dbdiagram.io to visualize")
        
        st.download_button("⬇️ Download DBML", data=dbml, file_name="logical_model.dbml", mime="text/plain")
    else:
        st.error("Please provide a logical model")
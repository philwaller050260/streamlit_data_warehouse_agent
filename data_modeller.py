import streamlit as st
from openai import OpenAI
import pandas as pd
import io

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

# Load CSV
def load_csv(uploaded_file) -> pd.DataFrame:
    return pd.read_csv(uploaded_file)

# Build column summary
def build_column_summary(df: pd.DataFrame) -> str:
    summary = "CSV Columns and sample data:\n\n"
    for col in df.columns:
        dtype = str(df[col].dtype)
        samples = df[col].dropna().head(3).tolist()
        summary += f"- {col} (type: {dtype}): {samples}\n"
    return summary

# Extract conceptual model from business case
def extract_from_business_case(client, business_case: str, model_id: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": """You are a senior data modeller. Analyse a business requirements document and extract the conceptual data model.

Your job is to identify:
1. ENTITIES - the main things/concepts being described (e.g., Customer, Order, Product)
2. ATTRIBUTES - the properties/characteristics of each entity (e.g., CustomerName, CustomerEmail)
3. REASONING - why each entity and attribute matters to the business

Format your response EXACTLY as follows:

ENTITIES IDENTIFIED:
- Entity1: Brief description of what it represents
- Entity2: Brief description of what it represents
...

ATTRIBUTES BY ENTITY:

Entity1
- attribute1: What it captures and why it matters
- attribute2: What it captures and why it matters
...

Entity2
- attribute1: What it captures and why it matters
...

RELATIONSHIPS:
- Entity1 relates to Entity2 via [relationship description]
...

BUSINESS JUSTIFICATION:
Brief paragraph explaining why this conceptual model answers the business questions in the requirements."""
            },
            {
                "role": "user",
                "content": f"Business case to analyse:\n\n{business_case}"
            }
        ],
        max_completion_tokens=2000
    )
    return response.choices[0].message.content

# Extract conceptual model from CSV
def extract_from_csv(client, column_summary: str, model_id: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": """You are a senior data modeller. Analyse a CSV file's columns and infer the conceptual data model.

Your job is to:
1. Group columns into ENTITIES (what real-world things do these columns describe?)
2. List ATTRIBUTES for each entity
3. Identify what BUSINESS PROCESSES or MEASUREMENTS are being captured
4. Suggest ADDITIONAL ATTRIBUTES that would be needed for a complete data warehouse

Format your response EXACTLY as follows:

ENTITIES INFERRED:
- Entity1: What real-world thing this represents based on the columns
- Entity2: What real-world thing this represents based on the columns
...

ATTRIBUTES BY ENTITY:

Entity1
- column_name: What this captures
- column_name: What this captures
...

Entity2
- column_name: What this captures
...

ADDITIONAL ATTRIBUTES RECOMMENDED:
These attributes should be added for complete tracking and auditability:

Entity1
- attribute_name: Why needed (e.g., "for audit trail", "for slowly-changing dimensions")
...

BUSINESS PROCESSES IDENTIFIED:
- Process1: What business event/transaction this data captures
- Process2: What business event/transaction this data captures
...

REASONING:
Brief paragraph on what business questions this data model can answer."""
            },
            {
                "role": "user",
                "content": f"CSV columns to analyse:\n\n{column_summary}"
            }
        ],
        max_completion_tokens=2000
    )
    return response.choices[0].message.content

# Main UI
st.title("📋 Data Modeller Agent")
st.caption("Extract entities and attributes from business cases or CSV files")

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

# Input method
input_method = st.radio("Choose input", ["Business Case (Text/Doc)", "CSV File"], horizontal=True)

if input_method == "Business Case (Text/Doc)":
    business_case = st.text_area("Paste your business case / requirements document:", height=250)
    
    if st.button("Extract Conceptual Model"):
        if business_case.strip():
            with st.spinner("Analysing business case..."):
                result = extract_from_business_case(client, business_case, model_id)
            
            st.markdown("### Conceptual Data Model")
            st.write(result)
            
            st.download_button(
                label="⬇️ Download as text",
                data=result,
                file_name="conceptual_model.txt",
                mime="text/plain"
            )
        else:
            st.error("Please enter a business case")

else:  # CSV file
    csv_file = st.file_uploader("Upload CSV file", type=["csv"])
    
    if csv_file:
        df = load_csv(csv_file)
        st.success(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        with st.expander("Preview data"):
            st.dataframe(df.head(5))
        
        if st.button("Extract Conceptual Model"):
            with st.spinner("Analysing CSV..."):
                column_summary = build_column_summary(df)
                result = extract_from_csv(client, column_summary, model_id)
            
            st.markdown("### Conceptual Data Model")
            st.write(result)
            
            st.download_button(
                label="⬇️ Download as text",
                data=result,
                file_name="conceptual_model.txt",
                mime="text/plain"
            )
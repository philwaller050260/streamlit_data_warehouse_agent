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

# Build logical model from conceptual model
def build_logical_model(client, conceptual_model: str, model_id: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": """You are a senior database architect. Convert a conceptual data model into a logical data model.

Your job is to:
1. Identify which entities are DIMENSIONS (descriptive) and which are FACTS (measurable events/transactions)
2. Add SURROGATE KEYS to every entity (e.g., CustomerKey INT IDENTITY)
3. Define FOREIGN KEY relationships between fact and dimension entities
4. Identify SLOWLY-CHANGING DIMENSION (SCD) requirements for each dimension
5. Specify CARDINALITY rules (1:1, 1:N, M:N) for each relationship
6. Recommend DENORMALISATION where appropriate for performance

Format your response EXACTLY as follows:

DIMENSIONAL ENTITIES:
- Entity1 (Dimension)
  - Surrogate Key: Entity1Key INT IDENTITY(1,1) PRIMARY KEY
  - Natural Key: original_id (business key from source)
  - Attributes: [list of attributes]
  - SCD Type: [Type 1 (overwrite), Type 2 (history), or Type 3 (limited history)]
  - Reason for SCD choice: [why this type makes sense]

- Entity2 (Dimension)
  - Surrogate Key: Entity2Key INT IDENTITY(1,1) PRIMARY KEY
  - Natural Key: original_id
  - Attributes: [list of attributes]
  - SCD Type: [Type]
  - Reason for SCD choice: [why]

FACT ENTITIES:
- FactEntity1 (Fact Table)
  - Surrogate Key: FactEntity1Key INT IDENTITY(1,1) PRIMARY KEY
  - Natural Key/Business Key: [what uniquely identifies a transaction]
  - Grain: [what one row represents - e.g., "one row per transaction", "one row per customer per day"]
  - Foreign Keys:
    * Entity1Key (FK to Entity1)
    * Entity2Key (FK to Entity2)
    * DateKey (FK to Dim_Date)
  - Measures/Metrics: [quantitative columns like amount, quantity, duration]

RELATIONSHIPS & CARDINALITY:
- FactEntity1 → Entity1: [Cardinality, e.g., "Many fact rows to one Entity1 record (M:1)"]
- FactEntity1 → Entity2: [Cardinality]
...

SPECIAL CONSIDERATIONS:
- Role-Playing Dimensions: [If any dimension appears in multiple roles (e.g., Branch as both PickupBranch and ReturnBranch, or Date as StartDate/EndDate/BookingDate), create SEPARATE LOGICAL ENTITIES for each role with identical structure but distinct names. This avoids ambiguity in fact table foreign keys. Example: Dim_DateStart, Dim_DateEnd, Dim_DateBooking - all identical structure, different names]
- Recommended Denormalisation: [Any attributes that should be denormalised from dimensions into facts for query performance]
- Audit Requirements: [Standard audit columns needed - CreatedDate, ModifiedDate, LoadDate, etc.]

LOGICAL MODEL RULES SUMMARY:
- All surrogate keys follow naming pattern: EntityName + "Key"
- All natural/business keys follow naming pattern: EntityName + "ID"
- All boolean columns are INT (1/0), not VARCHAR
- All date foreign keys are suffixed with "Key" (e.g., OrderDateKey)
- All measures in fact tables are DECIMAL or INT, never VARCHAR
- Every dimension has StartDate, EndDate, IsActive for SCD Type 2
- Every fact table has CreatedDate DATETIME for audit tracking"""
            },
            {
                "role": "user",
                "content": f"Conceptual model to convert to logical model:\n\n{conceptual_model}"
            }
        ],
        max_completion_tokens=2500
    )
    return response.choices[0].message.content

# Main UI
st.title("🔗 Logical Model Agent")
st.caption("Convert conceptual model into logical design with surrogate keys, FKs, and SCD rules")

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
st.subheader("Input: Conceptual Model")
st.caption("Upload the conceptual_model.txt file from the Data Modeller agent")

input_method = st.radio("Input method", ["Upload file", "Paste text"], horizontal=True)

conceptual_model = ""

if input_method == "Upload file":
    uploaded_file = st.file_uploader("Upload conceptual model (.txt)", type=["txt"])
    if uploaded_file:
        conceptual_model = uploaded_file.read().decode("utf-8")
        with st.expander("Preview conceptual model"):
            st.text(conceptual_model[:500] + ("..." if len(conceptual_model) > 500 else ""))
else:
    conceptual_model = st.text_area("Paste conceptual model:", height=250)

if st.button("Build Logical Model"):
    if conceptual_model.strip():
        with st.spinner("Designing logical model..."):
            logical_model = build_logical_model(client, conceptual_model, model_id)
        
        st.markdown("### Logical Data Model")
        st.write(logical_model)
        
        st.download_button(
            label="⬇️ Download as text",
            data=logical_model,
            file_name="logical_model.txt",
            mime="text/plain"
        )
    else:
        st.error("Please upload or paste a conceptual model")
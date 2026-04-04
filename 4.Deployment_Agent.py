import streamlit as st
import pymssql

st.title("🚀 Deploy Schema")
st.caption("Upload SQL schema and deploy to Azure SQL")

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

# Deploy SQL
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

# UI
try:
    st.info(f"Target: `{st.secrets['azure_sql_server']}` → `{st.secrets['azure_sql_database']}`")
except KeyError:
    st.error("❌ Azure SQL secrets not configured")

st.divider()

# Upload
sql_file = st.file_uploader("Upload SQL schema (.sql)", type=["sql", "txt"])
sql = sql_file.read().decode("utf-8") if sql_file else ""

if sql:
    with st.expander("Preview SQL"):
        st.code(sql[:800] + ("..." if len(sql) > 800 else ""), language="sql")

# Deploy
if st.button("🚀 Deploy", type="primary"):
    if sql.strip():
        with st.spinner("Deploying to Azure SQL..."):
            try:
                results = deploy_schema(sql)
                st.markdown("### Deployment Results")
                for r in results:
                    st.write(f"{r['status']} — `{r['statement']}...`")
                st.success("✅ Deployment complete!")
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
    else:
        st.error("Please upload a SQL file")
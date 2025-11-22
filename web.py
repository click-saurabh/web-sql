import os
import re
import pyodbc
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from datetime import datetime

# ========== CONFIG ==========
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")

LOGIN_USER = os.getenv("LOGIN_USER")
LOGIN_PASS = os.getenv("LOGIN_PASS")

# ========= SECURITY ==========
import logging
logging.disable(logging.CRITICAL)

# Block all modifying SQL
def is_safe_readonly_query(q):
    bad = ["insert", "update", "delete", "truncate", "drop", "alter"]
    return not any(b in q.lower() for b in bad)


# ========== DB CONNECTION ==========
def get_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};DATABASE={DB_DATABASE};"
        f"UID={DB_USER};PWD={DB_PASSWORD};"
        "Connection Timeout=5;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


# ========== HELPERS ==========
def get_categories():
    with get_connection() as conn:
        df = pd.read_sql("""
            SELECT DISTINCT 
                OQCN.CategoryId, 
                OQCN.CatName
            FROM OUQR
            INNER JOIN OQCN ON OUQR.QCategory = OQCN.CategoryId
            ORDER BY OQCN.CatName
        """, conn)
    return df.to_dict("records")


def get_queries(category_id):
    with get_connection() as conn:
        df = pd.read_sql(
            "SELECT DISTINCT QName FROM OUQR WHERE QCategory = ?",
            conn, params=[category_id]
        )
    return df["QName"].tolist()


def get_query_text(qname):
    with get_connection() as conn:
        df = pd.read_sql(
            "SELECT QString FROM OUQR WHERE QName = ?",
            conn, params=[qname]
        )
    return None if df.empty else df["QString"].iloc[0]


def execute_query(qstring, params):
    if not is_safe_readonly_query(qstring):
        raise Exception("⚠ Unsafe SQL blocked. Read-only mode enforced.")

    final_query = re.sub(r"\[%\d+\]", "?", qstring)
    final_query = re.sub(r"'\?'", "?", final_query)

    wrapped = f"SET NOCOUNT ON;\n{final_query}"

    with get_connection() as conn:
        df = pd.read_sql(wrapped, conn, params=params if params else None)

    return df


def extract_params(qstring):
    mapping = {}
    for line in qstring.splitlines():
        match = re.search(r"\[%(\d+)\]", line)
        if not match:
            continue

        idx = match.group(1)
        label = "Parameter " + idx
        l = line.lower()

        if "fromdate" in l:
            label = "From Date"
        elif "todate" in l:
            label = "To Date"
        elif "fromcard" in l:
            label = "From Customer"
        elif "tocard" in l:
            label = "To Customer"

        mapping[idx] = label

    return [(f"[%{k}]", v) for k, v in sorted(mapping.items(), key=lambda x: int(x[0]))]


def normalize_params(values):
    fixed = []
    for v in values:
        if isinstance(v, datetime):
            fixed.append(v.strftime("%Y-%m-%d"))
        else:
            fixed.append(v)
    return fixed


# ========== STREAMLIT UI ==========
st.set_page_config("Query Explorer", "📊", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "df" not in st.session_state:
    st.session_state.df = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "📋 Table"


# ---- LOGIN ----
if not st.session_state.logged_in:
    st.title("🔐 Login Required")

    usr = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if usr == LOGIN_USER and pwd == LOGIN_PASS:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()


# ---- SIDEBAR ----
st.sidebar.title("📂 SAP B1 Query Manager")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

search_text = st.sidebar.text_input("Search queries")


# ---- CATEGORY LIST ----
categories = get_categories()
for cat in categories:
    with st.sidebar.expander(cat["CatName"]):
        queries = get_queries(cat["CategoryId"])

        # search filter
        if search_text:
            queries = [q for q in queries if search_text.lower() in q.lower()]

        for q in queries:
            if st.button(q, key=f"{cat['CategoryId']}_{q}"):
                st.session_state.selected_query = q
                st.session_state.df = None


# ---- MAIN QUERY PROCESS ----
if "selected_query" in st.session_state:
    qname = st.session_state.selected_query
    qstring = get_query_text(qname)

    st.subheader(f"Query: {qname}")

    if not qstring:
        st.error("Query text not found.")
    else:
        params = extract_params(qstring)
        param_vals = []

        if params:
            st.info("Enter parameter values:")
            for placeholder, label in params:
                if "Date" in label:
                    v = st.date_input(label)
                else:
                    v = st.text_input(label)
                param_vals.append(v)

        if st.button("▶ Run Query"):
            try:
                fixed = normalize_params(param_vals)
                df = execute_query(qstring, fixed)
                st.session_state.df = df
            except Exception as e:
                st.error(str(e))


# ---- DISPLAY RESULTS + GRAPH ----
if st.session_state.df is not None:
    df = st.session_state.df

    if df.empty:
        st.warning("No results found.")
    else:
        st.success(f"{len(df)} rows returned")

        # Table vs Chart toggle
        view = st.radio(
            "View as:",
            ["📋 Table", "📊 Chart"],
            index=["📋 Table", "📊 Chart"].index(st.session_state.view_mode),
            key="view_mode"
        )

        # ------- TABLE -------
        if view == "📋 Table":
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Download CSV",
                csv,
                "results.csv",
                "text/csv"
            )

        # ------- CHART -------
        elif view == "📊 Chart":
            st.info("Select chart type and columns")

            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            all_cols = df.columns.tolist()

            chart_type = st.selectbox(
                "Chart Type",
                ["Bar", "Pie", "Line", "Scatter"]
            )

            fig = None

            if chart_type == "Pie":
                label_col = st.selectbox("Label Column", all_cols)
                value_col = st.selectbox("Value Column (numeric)", numeric_cols)

                if label_col and value_col:
                    fig = px.pie(df, names=label_col, values=value_col)

            else:
                x_col = st.selectbox("X-axis", all_cols)
                y_col = st.selectbox("Y-axis (numeric)", numeric_cols)

                if x_col and y_col:
                    if chart_type == "Bar":
                        fig = px.bar(df, x=x_col, y=y_col)
                    elif chart_type == "Line":
                        fig = px.line(df, x=x_col, y=y_col)
                    elif chart_type == "Scatter":
                        fig = px.scatter(df, x=x_col, y=y_col)

            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Select valid chart options.")

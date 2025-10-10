# # # import os
# # # import re
# # # import pyodbc
# # # import pandas as pd
# # # import streamlit as st
# # # import plotly.express as px
# # # from dotenv import load_dotenv
# # # from datetime import datetime

# # # # ========== CONFIG ==========
# # # load_dotenv()

# # # DB_USER = os.getenv("DB_USER")
# # # DB_PASSWORD = os.getenv("DB_PASSWORD")
# # # DB_SERVER = os.getenv("DB_SERVER")
# # # DB_DATABASE = os.getenv("DB_DATABASE")
# # # ROW_LIMIT = int(os.getenv("ROW_LIMIT", "1000"))

# # # LOGIN_USER = os.getenv("LOGIN_USER")
# # # LOGIN_PASS = os.getenv("LOGIN_PASS")


# # # # ========== DB CONNECTION ==========
# # # def get_connection():
# # #     conn_str = (
# # #         f"DRIVER={{ODBC Driver 17 for SQL Server}};"
# # #         f"SERVER={DB_SERVER};DATABASE={DB_DATABASE};"
# # #         f"UID={DB_USER};PWD={DB_PASSWORD}"
# # #     )
# # #     return pyodbc.connect(conn_str)


# # # # ========== HELPERS ==========
# # # def get_categories():
# # #     with get_connection() as conn:
# # #         df = pd.read_sql("SELECT DISTINCT QCategory FROM OUQR ORDER BY QCategory", conn)
# # #     return df["QCategory"].dropna().tolist()


# # # def get_queries(category_id):
# # #     with get_connection() as conn:
# # #         df = pd.read_sql(
# # #             "SELECT DISTINCT QName FROM OUQR WHERE QCategory = ?", conn, params=[category_id]
# # #         )
# # #     return df["QName"].tolist()


# # # def get_query_text(qname):
# # #     with get_connection() as conn:
# # #         df = pd.read_sql(
# # #             "SELECT QString FROM OUQR WHERE QName = ?", conn, params=[qname]
# # #         )
# # #     if df.empty:
# # #         return None
# # #     return df["QString"].iloc[0]


# # # def execute_query(qstring, params):
# # #     # Step 1: Replace SAP-style [%1], [%2] → ?
# # #     final_query = re.sub(r"\[%\d+\]", "?", qstring)

# # #     # Step 2: Replace quoted question marks ('?') with bare ?
# # #     final_query = re.sub(r"'\?'", "?", final_query)

# # #     # Wrap with row limit
# # #     wrapped = f"SET NOCOUNT ON; SET ROWCOUNT {ROW_LIMIT};\n{final_query}\nSET ROWCOUNT 0;"

# # #     with get_connection() as conn:
# # #         df = pd.read_sql(wrapped, conn, params=params if params else None)
# # #     return df


# # # def extract_params(qstring):
# # #     # Extract parameters like [%1], [%2] in order
# # #     matches = re.findall(r"\[%(\d+)\]", qstring)
# # #     return [f"param{m}" for m in matches]


# # # def normalize_params(param_values):
# # #     """Convert date-like strings to YYYY-MM-DD, keep others as-is."""
# # #     fixed_params = []
# # #     for val in param_values:
# # #         if isinstance(val, datetime):
# # #             fixed_params.append(val.strftime("%Y-%m-%d"))
# # #         else:
# # #             try:
# # #                 # detect DD/MM/YYYY or DD-MM-YYYY
# # #                 parsed = datetime.strptime(str(val), "%d/%m/%Y")
# # #                 fixed_params.append(parsed.strftime("%Y-%m-%d"))
# # #             except Exception:
# # #                 fixed_params.append(val)
# # #     return fixed_params


# # # # ========== STREAMLIT APP ==========
# # # st.set_page_config("Query Explorer", "📊", layout="wide")

# # # if "logged_in" not in st.session_state:
# # #     st.session_state.logged_in = False

# # # # ---- LOGIN ----
# # # if not st.session_state.logged_in:
# # #     st.title("🔐 Login")
# # #     username = st.text_input("Username")
# # #     password = st.text_input("Password", type="password")
# # #     if st.button("Login"):
# # #         if username == LOGIN_USER and password == LOGIN_PASS:
# # #             st.session_state.logged_in = True
# # #             st.experimental_rerun()
# # #         else:
# # #             st.error("Invalid username or password")
# # #     st.stop()

# # # # ---- SIDEBAR ----
# # # st.sidebar.title("📂 Query Explorer")
# # # st.sidebar.write("Logged in as:", LOGIN_USER)
# # # if st.sidebar.button("🚪 Logout"):
# # #     st.session_state.logged_in = False
# # #     st.experimental_rerun()

# # # # ---- MAIN LOGIC ----
# # # categories = get_categories()
# # # selected_cat = st.sidebar.selectbox("Select Category", categories)

# # # if selected_cat:
# # #     queries = get_queries(selected_cat)
# # #     qname = st.sidebar.selectbox("Select Query", queries)

# # #     if qname:
# # #         st.subheader(f"📝 Query: {qname}")
# # #         qstring = get_query_text(qname)

# # #         if not qstring:
# # #             st.error("Query not found.")
# # #         else:
# # #             st.code(qstring, language="sql")

# # #             # Params detection
# # #             params = extract_params(qstring)
# # #             param_values = []
# # #             if params:
# # #                 st.info("Enter parameter values:")
# # #                 for p in params:
# # #                     if "date" in qstring.lower():
# # #                         # show calendar input for date-like parameters
# # #                         val = st.date_input(p)
# # #                         param_values.append(val)
# # #                     else:
# # #                         val = st.text_input(p, "")
# # #                         param_values.append(val)

# # #             # Run button
# # #             if st.button("▶ Run Query"):
# # #                 try:
# # #                     fixed_params = normalize_params(param_values)
# # #                     df = execute_query(qstring, fixed_params)
# # #                     if df.empty:
# # #                         st.warning("No results found.")
# # #                     else:
# # #                         st.success(f"Returned {len(df)} rows")

# # #                         view = st.radio(
# # #                             "View as:", ["📋 Table", "📊 Chart"], horizontal=True
# # #                         )

# # #                         if view == "📋 Table":
# # #                             st.dataframe(df)
# # #                         else:
# # #                             # Auto-detect chart columns
# # #                             numeric_cols = df.select_dtypes(include="number").columns.tolist()
# # #                             text_cols = df.select_dtypes(exclude="number").columns.tolist()

# # #                             if len(numeric_cols) >= 1 and len(text_cols) >= 1:
# # #                                 fig = px.bar(df, x=text_cols[0], y=numeric_cols[0])
# # #                                 st.plotly_chart(fig, use_container_width=True)
# # #                             else:
# # #                                 st.info(
# # #                                     "Need at least one numeric and one text column to render chart."
# # #                                 )
# # #                 except Exception as e:
# # #                     st.error(f"Error: {e}")




# # # import os
# # # import re
# # # import pyodbc
# # # import pandas as pd
# # # import streamlit as st
# # # import plotly.express as px
# # # from dotenv import load_dotenv
# # # from datetime import datetime

# # # # ========== CONFIG ==========
# # # load_dotenv()

# # # DB_USER = os.getenv("DB_USER")
# # # DB_PASSWORD = os.getenv("DB_PASSWORD")
# # # DB_SERVER = os.getenv("DB_SERVER")
# # # DB_DATABASE = os.getenv("DB_DATABASE")
# # # ROW_LIMIT = int(os.getenv("ROW_LIMIT", "1000"))

# # # LOGIN_USER = os.getenv("LOGIN_USER")
# # # LOGIN_PASS = os.getenv("LOGIN_PASS")


# # # # ========== DB CONNECTION ==========
# # # def get_connection():
# # #     conn_str = (
# # #         f"DRIVER={{ODBC Driver 17 for SQL Server}};"
# # #         f"SERVER={DB_SERVER};DATABASE={DB_DATABASE};"
# # #         f"UID={DB_USER};PWD={DB_PASSWORD}"
# # #     )
# # #     return pyodbc.connect(conn_str)


# # # # ========== HELPERS ==========
# # # def get_categories():
# # #     with get_connection() as conn:
# # #         df = pd.read_sql("SELECT DISTINCT QCategory FROM OUQR ORDER BY QCategory", conn)
# # #     return df["QCategory"].dropna().tolist()


# # # def get_queries(category_id):
# # #     with get_connection() as conn:
# # #         df = pd.read_sql(
# # #             "SELECT DISTINCT QName FROM OUQR WHERE QCategory = ?", conn, params=[category_id]
# # #         )
# # #     return df["QName"].tolist()


# # # def get_query_text(qname):
# # #     with get_connection() as conn:
# # #         df = pd.read_sql(
# # #             "SELECT QString FROM OUQR WHERE QName = ?", conn, params=[qname]
# # #         )
# # #     if df.empty:
# # #         return None
# # #     return df["QString"].iloc[0]


# # # def execute_query(qstring, params):
# # #     # Step 1: Replace SAP-style [%1], [%2] → ?
# # #     final_query = re.sub(r"\[%\d+\]", "?", qstring)

# # #     # Step 2: Replace quoted question marks ('?') with bare ?
# # #     final_query = re.sub(r"'\?'", "?", final_query)

# # #     # Wrap with row limit
# # #     wrapped = f"SET NOCOUNT ON; SET ROWCOUNT {ROW_LIMIT};\n{final_query}\nSET ROWCOUNT 0;"

# # #     with get_connection() as conn:
# # #         df = pd.read_sql(wrapped, conn, params=params if params else None)
# # #     return df


# # # def extract_params(qstring):
# # #     # Extract parameters like [%1], [%2] in order
# # #     matches = re.findall(r"\[%(\d+)\]", qstring)
# # #     return [f"param{m}" for m in matches]


# # # def normalize_params(param_values):
# # #     """Convert date-like strings to YYYY-MM-DD, keep others as-is."""
# # #     fixed_params = []
# # #     for val in param_values:
# # #         if isinstance(val, datetime):
# # #             fixed_params.append(val.strftime("%Y-%m-%d"))
# # #         else:
# # #             try:
# # #                 # detect DD/MM/YYYY
# # #                 parsed = datetime.strptime(str(val), "%d/%m/%Y")
# # #                 fixed_params.append(parsed.strftime("%Y-%m-%d"))
# # #             except Exception:
# # #                 fixed_params.append(val)
# # #     return fixed_params


# # # # ========== STREAMLIT APP ==========
# # # st.set_page_config("Query Explorer", "📊", layout="wide")

# # # if "logged_in" not in st.session_state:
# # #     st.session_state.logged_in = False

# # # # ---- LOGIN ----
# # # if not st.session_state.logged_in:
# # #     st.title("🔐 Login")
# # #     username = st.text_input("Username")
# # #     password = st.text_input("Password", type="password")
# # #     if st.button("Login"):
# # #         if username == LOGIN_USER and password == LOGIN_PASS:
# # #             st.session_state.logged_in = True
# # #             st.experimental_rerun()
# # #         else:
# # #             st.error("Invalid username or password")
# # #     st.stop()

# # # # ---- SIDEBAR ----
# # # st.sidebar.title("📂 Query Explorer")
# # # st.sidebar.write("Logged in as:", LOGIN_USER)
# # # if st.sidebar.button("🚪 Logout"):
# # #     st.session_state.logged_in = False
# # #     st.experimental_rerun()

# # # # ---- MAIN LOGIC ----
# # # categories = get_categories()
# # # selected_cat = st.sidebar.selectbox("Select Category", categories)

# # # if selected_cat:
# # #     queries = get_queries(selected_cat)
# # #     qname = st.sidebar.selectbox("Select Query", queries)

# # #     if qname:
# # #         st.subheader(f"📝 Query: {qname}")
# # #         qstring = get_query_text(qname)

# # #         if not qstring:
# # #             st.error("Query not found.")
# # #         else:
# # #             st.code(qstring, language="sql")

# # #             # Params detection
# # #             params = extract_params(qstring)
# # #             param_values = []
# # #             if params:
# # #                 st.info("Enter parameter values:")
# # #                 for p in params:
# # #                     if "date" in qstring.lower():
# # #                         # show calendar input for date-like parameters
# # #                         val = st.date_input(p)
# # #                         param_values.append(val)
# # #                     else:
# # #                         val = st.text_input(p, "")
# # #                         param_values.append(val)

# # #             # Run button
# # #             if st.button("▶ Run Query"):
# # #                 try:
# # #                     fixed_params = normalize_params(param_values)
# # #                     df = execute_query(qstring, fixed_params)
# # #                     if df.empty:
# # #                         st.warning("No results found.")
# # #                     else:
# # #                         st.success(f"Returned {len(df)} rows")

# # #                         # Compatible radio (horizontal if supported)
# # #                         try:
# # #                             view = st.radio(
# # #                                 "View as:", ["📋 Table", "📊 Chart"], horizontal=True
# # #                             )
# # #                         except TypeError:
# # #                             view = st.radio(
# # #                                 "View as:", ["📋 Table", "📊 Chart"]
# # #                             )

# # #                         if view == "📋 Table":
# # #                             st.dataframe(df)
# # #                         else:
# # #                             # Auto-detect chart columns
# # #                             numeric_cols = df.select_dtypes(include="number").columns.tolist()
# # #                             text_cols = df.select_dtypes(exclude="number").columns.tolist()

# # #                             if len(numeric_cols) >= 1 and len(text_cols) >= 1:
# # #                                 fig = px.bar(df, x=text_cols[0], y=numeric_cols[0])
# # #                                 st.plotly_chart(fig, use_container_width=True)
# # #                             else:
# # #                                 st.info(
# # #                                     "Need at least one numeric and one text column to render chart."
# # #                                 )
# # #                 except Exception as e:
# # #                     st.error(f"Error: {e}")




# # import os
# # import re
# # import pyodbc
# # import pandas as pd
# # import streamlit as st
# # import plotly.express as px
# # from dotenv import load_dotenv
# # from datetime import datetime

# # # ========== CONFIG ==========
# # load_dotenv()

# # DB_USER = os.getenv("DB_USER")
# # DB_PASSWORD = os.getenv("DB_PASSWORD")
# # DB_SERVER = os.getenv("DB_SERVER")
# # DB_DATABASE = os.getenv("DB_DATABASE")

# # LOGIN_USER = os.getenv("LOGIN_USER")
# # LOGIN_PASS = os.getenv("LOGIN_PASS")


# # # ========== DB CONNECTION ==========
# # def get_connection():
# #     conn_str = (
# #         f"DRIVER={{ODBC Driver 17 for SQL Server}};"
# #         f"SERVER={DB_SERVER};DATABASE={DB_DATABASE};"
# #         f"UID={DB_USER};PWD={DB_PASSWORD}"
# #     )
# #     return pyodbc.connect(conn_str)


# # # ========== HELPERS ==========
# # def get_categories():
# #     with get_connection() as conn:
# #         df = pd.read_sql("SELECT DISTINCT QCategory FROM OUQR ORDER BY QCategory", conn)
# #     return df["QCategory"].dropna().tolist()


# # def get_queries(category_id):
# #     with get_connection() as conn:
# #         df = pd.read_sql(
# #             "SELECT DISTINCT QName FROM OUQR WHERE QCategory = ?", conn, params=[category_id]
# #         )
# #     return df["QName"].tolist()


# # def get_query_text(qname):
# #     with get_connection() as conn:
# #         df = pd.read_sql(
# #             "SELECT QString FROM OUQR WHERE QName = ?", conn, params=[qname]
# #         )
# #     if df.empty:
# #         return None
# #     return df["QString"].iloc[0]


# # def execute_query(qstring, params):
# #     # Step 1: Replace SAP-style [%1], [%2] → ?
# #     final_query = re.sub(r"\[%\d+\]", "?", qstring)

# #     # Step 2: Replace quoted question marks ('?') with bare ?
# #     final_query = re.sub(r"'\?'", "?", final_query)

# #     # No row limit → fetch all
# #     wrapped = f"SET NOCOUNT ON;\n{final_query}"

# #     with get_connection() as conn:
# #         df = pd.read_sql(wrapped, conn, params=params if params else None)
# #     return df


# # def extract_params(qstring):
# #     # Extract parameters like [%1], [%2] in order
# #     matches = re.findall(r"\[%(\d+)\]", qstring)
# #     return [f"param{m}" for m in matches]


# # def normalize_params(param_values):
# #     """Convert date-like strings to YYYY-MM-DD, keep others as-is."""
# #     fixed_params = []
# #     for val in param_values:
# #         if isinstance(val, datetime):
# #             fixed_params.append(val.strftime("%Y-%m-%d"))
# #         else:
# #             try:
# #                 parsed = datetime.strptime(str(val), "%d/%m/%Y")
# #                 fixed_params.append(parsed.strftime("%Y-%m-%d"))
# #             except Exception:
# #                 fixed_params.append(val)
# #     return fixed_params


# # # ========== STREAMLIT APP ==========
# # st.set_page_config("Query Explorer", "📊", layout="wide")

# # if "logged_in" not in st.session_state:
# #     st.session_state.logged_in = False

# # # ---- LOGIN ----
# # if not st.session_state.logged_in:
# #     st.title("🔐 Login")
# #     username = st.text_input("Username")
# #     password = st.text_input("Password", type="password")
# #     if st.button("Login"):
# #         if username == LOGIN_USER and password == LOGIN_PASS:
# #             st.session_state.logged_in = True
# #             st.experimental_rerun()
# #         else:
# #             st.error("Invalid username or password")
# #     st.stop()

# # # ---- SIDEBAR ----
# # st.sidebar.title("📂 Query Explorer")
# # st.sidebar.write("Logged in as:", LOGIN_USER)
# # if st.sidebar.button("🚪 Logout"):
# #     st.session_state.logged_in = False
# #     st.experimental_rerun()

# # # ---- MAIN LOGIC ----
# # categories = get_categories()
# # selected_cat = st.sidebar.selectbox("Select Category", categories)

# # if selected_cat:
# #     queries = get_queries(selected_cat)
# #     qname = st.sidebar.selectbox("Select Query", queries)

# #     if qname:
# #         st.subheader(f"📝 Query: {qname}")
# #         qstring = get_query_text(qname)

# #         if not qstring:
# #             st.error("Query not found.")
# #         else:
# #             st.code(qstring, language="sql")

# #             # Params detection
# #             params = extract_params(qstring)
# #             param_values = []
# #             if params:
# #                 st.info("Enter parameter values:")
# #                 for p in params:
# #                     if "date" in qstring.lower():
# #                         val = st.date_input(p)
# #                         param_values.append(val)
# #                     else:
# #                         val = st.text_input(p, "")
# #                         param_values.append(val)

# #             # Run button
# #             if st.button("▶ Run Query"):
# #                 try:
# #                     fixed_params = normalize_params(param_values)
# #                     df = execute_query(qstring, fixed_params)
# #                     if df.empty:
# #                         st.warning("No results found.")
# #                     else:
# #                         st.success(f"Returned {len(df)} rows")

# #                         # Compatible radio (horizontal if supported)
# #                         try:
# #                             view = st.radio(
# #                                 "View as:", ["📋 Table", "📊 Chart"], horizontal=True
# #                             )
# #                         except TypeError:
# #                             view = st.radio(
# #                                 "View as:", ["📋 Table", "📊 Chart"]
# #                             )

# #                         # ===== TABLE VIEW =====
# #                         if view == "📋 Table":
# #                             st.dataframe(df)

# #                             # Export options
# #                             csv = df.to_csv(index=False).encode("utf-8")
# #                             excel = df.to_excel("data.xlsx", index=False, engine="openpyxl")
# #                             st.download_button(
# #                                 "⬇ Download CSV", csv, "data.csv", "text/csv"
# #                             )

# #                         # ===== CHART VIEW =====
# #                         else:
# #                             st.info("Select columns and chart type:")

# #                             numeric_cols = df.select_dtypes(include="number").columns.tolist()
# #                             text_cols = df.select_dtypes(exclude="number").columns.tolist()

# #                             x_col = st.selectbox("X-axis", df.columns, index=0)
# #                             y_col = st.selectbox("Y-axis", df.columns, index=1 if len(df.columns) > 1 else 0)
# #                             chart_type = st.selectbox("Chart Type", ["Bar", "Pie", "Scatter", "Line"])

# #                             fig = None
# #                             if chart_type == "Bar":
# #                                 fig = px.bar(df, x=x_col, y=y_col)
# #                             elif chart_type == "Pie":
# #                                 fig = px.pie(df, names=x_col, values=y_col)
# #                             elif chart_type == "Scatter":
# #                                 fig = px.scatter(df, x=x_col, y=y_col)
# #                             elif chart_type == "Line":
# #                                 fig = px.line(df, x=x_col, y=y_col)

# #                             if fig:
# #                                 st.plotly_chart(fig, use_container_width=True)

# #                 except Exception as e:
# #                     st.error(f"Error: {e}")



# import os
# import re
# import pyodbc
# import pandas as pd
# import streamlit as st
# import plotly.express as px
# from dotenv import load_dotenv
# from datetime import datetime

# # ========== CONFIG ==========
# load_dotenv()

# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_SERVER = os.getenv("DB_SERVER")
# DB_DATABASE = os.getenv("DB_DATABASE")

# LOGIN_USER = os.getenv("LOGIN_USER")
# LOGIN_PASS = os.getenv("LOGIN_PASS")


# # ========== DB CONNECTION ==========
# def get_connection():
#     conn_str = (
#         f"DRIVER={{ODBC Driver 17 for SQL Server}};"
#         f"SERVER={DB_SERVER};DATABASE={DB_DATABASE};"
#         f"UID={DB_USER};PWD={DB_PASSWORD}"
#     )
#     return pyodbc.connect(conn_str)


# # ========== HELPERS ==========
# def get_categories():
#     with get_connection() as conn:
#         df = pd.read_sql("SELECT DISTINCT QCategory FROM OUQR ORDER BY QCategory", conn)
#     return df["QCategory"].dropna().tolist()


# def get_queries(category_id):
#     with get_connection() as conn:
#         df = pd.read_sql(
#             "SELECT DISTINCT QName FROM OUQR WHERE QCategory = ?", conn, params=[category_id]
#         )
#     return df["QName"].tolist()


# def get_query_text(qname):
#     with get_connection() as conn:
#         df = pd.read_sql(
#             "SELECT QString FROM OUQR WHERE QName = ?", conn, params=[qname]
#         )
#     if df.empty:
#         return None
#     return df["QString"].iloc[0]


# def execute_query(qstring, params):
#     final_query = re.sub(r"\[%\d+\]", "?", qstring)
#     final_query = re.sub(r"'\?'", "?", final_query)

#     wrapped = f"SET NOCOUNT ON;\n{final_query}"
#     with get_connection() as conn:
#         df = pd.read_sql(wrapped, conn, params=params if params else None)
#     return df


# def extract_params(qstring):
#     matches = re.findall(r"\[%(\d+)\]", qstring)
#     return [f"param{m}" for m in matches]


# def normalize_params(param_values):
#     fixed_params = []
#     for val in param_values:
#         if isinstance(val, datetime):
#             fixed_params.append(val.strftime("%Y-%m-%d"))
#         else:
#             try:
#                 parsed = datetime.strptime(str(val), "%d/%m/%Y")
#                 fixed_params.append(parsed.strftime("%Y-%m-%d"))
#             except Exception:
#                 fixed_params.append(val)
#     return fixed_params


# # ========== STREAMLIT APP ==========
# st.set_page_config("Query Explorer", "📊", layout="wide")

# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False
# if "df" not in st.session_state:
#     st.session_state.df = None
# if "view_mode" not in st.session_state:
#     st.session_state.view_mode = "📋 Table"

# # ---- LOGIN ----
# if not st.session_state.logged_in:
#     st.title("🔐 Login")
#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")
#     if st.button("Login"):
#         if username == LOGIN_USER and password == LOGIN_PASS:
#             st.session_state.logged_in = True
#             st.experimental_rerun()
#         else:
#             st.error("Invalid username or password")
#     st.stop()

# # ---- SIDEBAR ----
# st.sidebar.title("📂 Query Explorer")
# st.sidebar.write("Logged in as:", LOGIN_USER)
# if st.sidebar.button("🚪 Logout"):
#     st.session_state.logged_in = False
#     st.experimental_rerun()

# # ---- MAIN LOGIC ----
# categories = get_categories()
# selected_cat = st.sidebar.selectbox("Select Category", categories)

# if selected_cat:
#     queries = get_queries(selected_cat)
#     qname = st.sidebar.selectbox("Select Query", queries)

#     if qname:
#         st.subheader(f"📝 Query: {qname}")
#         qstring = get_query_text(qname)

#         if not qstring:
#             st.error("Query not found.")
#         else:
#             st.code(qstring, language="sql")

#             # Params detection
#             params = extract_params(qstring)
#             param_values = []
#             if params:
#                 st.info("Enter parameter values:")
#                 for p in params:
#                     if "date" in qstring.lower():
#                         val = st.date_input(p)
#                         param_values.append(val)
#                     else:
#                         val = st.text_input(p, "")
#                         param_values.append(val)

#             # Run button
#             if st.button("▶ Run Query"):
#                 try:
#                     fixed_params = normalize_params(param_values)
#                     df = execute_query(qstring, fixed_params)
#                     st.session_state.df = df
#                 except Exception as e:
#                     st.error(f"Error: {e}")

#         # ========== DISPLAY RESULTS ==========
#         if st.session_state.df is not None:
#             df = st.session_state.df

#             if df.empty:
#                 st.warning("No results found.")
#             else:
#                 st.success(f"Returned {len(df)} rows")

#                 # Persist view selection
#                 view = st.radio(
#                     "View as:",
#                     ["📋 Table", "📊 Chart"],
#                     index=["📋 Table", "📊 Chart"].index(st.session_state.view_mode),
#                     key="view_mode"
#                 )

#                 # ===== TABLE VIEW =====
#                 if view == "📋 Table":
#                     st.dataframe(df)

#                     csv = df.to_csv(index=False).encode("utf-8")
#                     st.download_button(
#                         "⬇ Download CSV", csv, "data.csv", "text/csv"
#                     )

#                 # # ===== CHART VIEW =====
#                 # elif view == "📊 Chart":
#                 #     st.info("Select columns and chart type:")

#                 #     numeric_cols = df.select_dtypes(include="number").columns.tolist()
#                 #     all_cols = df.columns.tolist()

#                 #     chart_type = st.selectbox("Chart Type", ["Bar", "Pie", "Scatter", "Line"])

#                 #     fig = None
#                 #     if chart_type == "Pie":
#                 #         label_col = st.selectbox("Label Column", all_cols)
#                 #         value_col = st.selectbox("Value Column (numeric)", numeric_cols)
#                 #         if value_col:
#                 #             fig = px.pie(df, names=label_col, values=value_col)

#                 #         else:
#                 #             x_col = st.selectbox("X-axis", all_cols, index=0)
#                 #             y_col = st.selectbox(
#                 #             "Y-axis (numeric)", numeric_cols,
#                 #             index=0 if numeric_cols else None
#                 #         )
#                 #         if y_col:
#                 #             if chart_type == "Bar":
#                 #                 fig = px.bar(df, x=x_col, y=y_col)
#                 #             elif chart_type == "Scatter":
#                 #                 fig = px.scatter(df, x=x_col, y=y_col)
#                 #             elif chart_type == "Line":
#                 #                 fig = px.line(df, x=x_col, y=y_col)

#                 #         if fig:
#                 #             st.plotly_chart(fig, use_container_width=True)
#                 #     else:
#                 #         st.warning("Please select valid columns for the chart.")
#                 # ===== CHART VIEW =====
#                 elif view == "📊 Chart":
#                     st.info("Select columns and chart type:")

#                     numeric_cols = df.select_dtypes(include="number").columns.tolist()
#                     all_cols = df.columns.tolist()

#                     chart_type = st.selectbox("Chart Type", ["Bar", "Pie", "Scatter", "Line"])

#                     fig = None
#                     if chart_type == "Pie":
#                         label_col = st.selectbox("Label Column", all_cols)
#                         value_col = st.selectbox("Value Column (numeric)", numeric_cols)
#                         if label_col and value_col:
#                             fig = px.pie(df, names=label_col, values=value_col)

#                     elif chart_type in ["Bar", "Scatter", "Line"]:
#                             x_col = st.selectbox("X-axis", all_cols, index=0)
#                             y_col = st.selectbox(
#                                 "Y-axis (numeric)", numeric_cols,
#                                 index=0 if numeric_cols else None
#                             )
#                             if x_col and y_col:
#                                 if chart_type == "Bar":
#                                     fig = px.bar(df, x=x_col, y=y_col)
#                                 elif chart_type == "Scatter":
#                                     fig = px.scatter(df, x=x_col, y=y_col)
#                                 elif chart_type == "Line":
#                                     fig = px.line(df, x=x_col, y=y_col)

#                             if fig:
#                                 st.plotly_chart(fig, use_container_width=True)
#                     else:
#                         st.warning("Please select valid columns for the chart.")



# import os
# import re
# import pyodbc
# import pandas as pd
# import streamlit as st
# import plotly.express as px
# from dotenv import load_dotenv
# from datetime import datetime

# # ========== CONFIG ==========
# load_dotenv()

# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_SERVER = os.getenv("DB_SERVER")
# DB_DATABASE = os.getenv("DB_DATABASE")

# LOGIN_USER = os.getenv("LOGIN_USER")
# LOGIN_PASS = os.getenv("LOGIN_PASS")


# # ========== DB CONNECTION ==========
# def get_connection():
#     conn_str = (
#         f"DRIVER={{ODBC Driver 17 for SQL Server}};"
#         f"SERVER={DB_SERVER};DATABASE={DB_DATABASE};"
#         f"UID={DB_USER};PWD={DB_PASSWORD}"
#     )
#     return pyodbc.connect(conn_str)


# # ========== HELPERS ==========
# def get_categories():
#     with get_connection() as conn:
#         df = pd.read_sql("SELECT DISTINCT QCategory FROM OUQR ORDER BY QCategory", conn)
#     return df["QCategory"].dropna().tolist()


# def get_queries(category_id):
#     with get_connection() as conn:
#         df = pd.read_sql(
#             "SELECT DISTINCT QName FROM OUQR WHERE QCategory = ?", conn, params=[category_id]
#         )
#     return df["QName"].tolist()


# def get_query_text(qname):
#     with get_connection() as conn:
#         df = pd.read_sql(
#             "SELECT QString FROM OUQR WHERE QName = ?", conn, params=[qname]
#         )
#     if df.empty:
#         return None
#     return df["QString"].iloc[0]


# def execute_query(qstring, params):
#     final_query = re.sub(r"\[%\d+\]", "?", qstring)
#     final_query = re.sub(r"'\?'", "?", final_query)

#     wrapped = f"SET NOCOUNT ON;\n{final_query}"
#     with get_connection() as conn:
#         df = pd.read_sql(wrapped, conn, params=params if params else None)
#     return df


# def extract_params(qstring):
#     matches = re.findall(r"\[%(\d+)\]", qstring)
#     return [f"param{m}" for m in matches]


# def normalize_params(param_values):
#     fixed_params = []
#     for val in param_values:
#         if isinstance(val, datetime):
#             fixed_params.append(val.strftime("%Y-%m-%d"))
#         else:
#             try:
#                 parsed = datetime.strptime(str(val), "%d/%m/%Y")
#                 fixed_params.append(parsed.strftime("%Y-%m-%d"))
#             except Exception:
#                 fixed_params.append(val)
#     return fixed_params


# # ========== STREAMLIT APP ==========
# st.set_page_config("Query Explorer", "📊", layout="wide")

# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False
# if "df" not in st.session_state:
#     st.session_state.df = None
# if "view_mode" not in st.session_state:
#     st.session_state.view_mode = "📋 Table"

# # ---- LOGIN ----
# if not st.session_state.logged_in:
#     st.title("🔐 Login")
#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")
#     if st.button("Login"):
#         if username == LOGIN_USER and password == LOGIN_PASS:
#             st.session_state.logged_in = True
#             st.experimental_rerun()
#         else:
#             st.error("Invalid username or password")
#     st.stop()

# # ---- SIDEBAR ----
# st.sidebar.title("📂 Query Explorer")
# st.sidebar.write("Logged in as:", LOGIN_USER)
# if st.sidebar.button("🚪 Logout"):
#     st.session_state.logged_in = False
#     st.experimental_rerun()

# # ---- MAIN LOGIC ----
# categories = get_categories()
# selected_cat = st.sidebar.selectbox("Select Category", categories)

# if selected_cat:
#     queries = get_queries(selected_cat)
#     qname = st.sidebar.selectbox("Select Query", queries)

#     if qname:
#         st.subheader(f"📝 Query: {qname}")
#         qstring = get_query_text(qname)

#         if not qstring:
#             st.error("Query not found.")
#         else:
#             st.code(qstring, language="sql")

#             # Params detection
#             params = extract_params(qstring)
#             param_values = []
#             if params:
#                 st.info("Enter parameter values:")
#                 for p in params:
#                     if "date" in qstring.lower():
#                         val = st.date_input(p)
#                         param_values.append(val)
#                     else:
#                         val = st.text_input(p, "")
#                         param_values.append(val)

#             # Run button
#             if st.button("▶ Run Query"):
#                 try:
#                     fixed_params = normalize_params(param_values)
#                     df = execute_query(qstring, fixed_params)
#                     st.session_state.df = df
#                 except Exception as e:
#                     st.error(f"Error: {e}")

#         # ========== DISPLAY RESULTS ==========
#         if st.session_state.df is not None:
#             df = st.session_state.df

#             if df.empty:
#                 st.warning("No results found.")
#             else:
#                 st.success(f"Returned {len(df)} rows")

#                 # Persist view selection
#                 view = st.radio(
#                     "View as:",
#                     ["📋 Table", "📊 Chart"],
#                     index=["📋 Table", "📊 Chart"].index(st.session_state.view_mode),
#                     key="view_mode"
#                 )

#                 # ===== TABLE VIEW =====
#                 if view == "📋 Table":
#                     st.dataframe(df)

#                     csv = df.to_csv(index=False).encode("utf-8")
#                     st.download_button(
#                         "⬇ Download CSV", csv, "data.csv", "text/csv"
#                     )

#                 # ===== CHART VIEW =====
#                 elif view == "📊 Chart":
#                     st.info("Select columns and chart type:")

#                     numeric_cols = df.select_dtypes(include="number").columns.tolist()
#                     all_cols = df.columns.tolist()

#                     chart_type = st.selectbox("Chart Type", ["Bar", "Pie", "Scatter", "Line"])

#                     fig = None
#                     if chart_type == "Pie":
#                         label_col = st.selectbox("Label Column", all_cols, key="pie_label")
#                         value_col = st.selectbox("Value Column (numeric)", numeric_cols, key="pie_value")

#                         if label_col and value_col:
#                             fig = px.pie(df, names=label_col, values=value_col)

#                     elif chart_type in ["Bar", "Scatter", "Line"]:
#                         x_col = st.selectbox("X-axis", all_cols, index=0, key="x_axis")
#                         y_col = st.selectbox("Y-axis (numeric)", numeric_cols, key="y_axis")

#                         if x_col and y_col:
#                             if chart_type == "Bar":
#                                 fig = px.bar(df, x=x_col, y=y_col)
#                             elif chart_type == "Scatter":
#                                 fig = px.scatter(df, x=x_col, y=y_col)
#                             elif chart_type == "Line":
#                                 fig = px.line(df, x=x_col, y=y_col)

#                     if fig:
#                         st.plotly_chart(fig, use_container_width=True)
#                     else:
#                         st.warning("Please select valid columns for the chart.")




# import os
# import re
# import pyodbc
# import pandas as pd
# import streamlit as st
# import plotly.express as px
# from dotenv import load_dotenv
# from datetime import datetime

# # ========== CONFIG ==========
# load_dotenv()

# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_SERVER = os.getenv("DB_SERVER")
# DB_DATABASE = os.getenv("DB_DATABASE")

# LOGIN_USER = os.getenv("LOGIN_USER")
# LOGIN_PASS = os.getenv("LOGIN_PASS")

# # ========== DB CONNECTION ==========
# def get_connection():
#     conn_str = (
#         f"DRIVER={{ODBC Driver 17 for SQL Server}};"
#         f"SERVER={DB_SERVER};DATABASE={DB_DATABASE};"
#         f"UID={DB_USER};PWD={DB_PASSWORD}"
#     )
#     return pyodbc.connect(conn_str)

# # ========== HELPERS ==========
# def get_categories():
#     with get_connection() as conn:
#         df = pd.read_sql("SELECT DISTINCT QCategory FROM OUQR ORDER BY QCategory", conn)
#     return df["QCategory"].dropna().tolist()

# def get_queries(category_id):
#     with get_connection() as conn:
#         df = pd.read_sql(
#             "SELECT DISTINCT QName FROM OUQR WHERE QCategory = ?", conn, params=[category_id]
#         )
#     return df["QName"].tolist()

# def get_query_text(qname):
#     with get_connection() as conn:
#         df = pd.read_sql(
#             "SELECT QString FROM OUQR WHERE QName = ?", conn, params=[qname]
#         )
#     if df.empty:
#         return None
#     return df["QString"].iloc[0]

# def execute_query(qstring, params):
#     final_query = re.sub(r"\[%\d+\]", "?", qstring)
#     final_query = re.sub(r"'\?'", "?", final_query)
#     wrapped = f"SET NOCOUNT ON;\n{final_query}"
#     with get_connection() as conn:
#         df = pd.read_sql(wrapped, conn, params=params if params else None)
#     return df

# def extract_params(qstring):
#     matches = re.findall(r"\[%(\d+)\]", qstring)
#     return [f"param{m}" for m in matches]

# def normalize_params(param_values):
#     fixed_params = []
#     for val in param_values:
#         if isinstance(val, datetime):
#             fixed_params.append(val.strftime("%Y-%m-%d"))
#         else:
#             try:
#                 parsed = datetime.strptime(str(val), "%d/%m/%Y")
#                 fixed_params.append(parsed.strftime("%Y-%m-%d"))
#             except Exception:
#                 fixed_params.append(val)
#     return fixed_params

# # ========== STREAMLIT APP ==========
# st.set_page_config("Query Explorer", "📊", layout="wide")

# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False
# if "df" not in st.session_state:
#     st.session_state.df = None
# if "view_mode" not in st.session_state:
#     st.session_state.view_mode = "📋 Table"
# if "selected_query" not in st.session_state:
#     st.session_state.selected_query = None

# # ---- LOGIN ----
# if not st.session_state.logged_in:
#     st.title("🔐 Login")
#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")
#     if st.button("Login"):
#         if username == LOGIN_USER and password == LOGIN_PASS:
#             st.session_state.logged_in = True
#             st.experimental_rerun()
#         else:
#             st.error("Invalid username or password")
#     st.stop()

# # ---- SIDEBAR (Drawer) ----
# st.sidebar.title("📂 Query Explorer")
# st.sidebar.write("Logged in as:", LOGIN_USER)
# if st.sidebar.button("🚪 Logout"):
#     st.session_state.logged_in = False
#     st.experimental_rerun()

# # 🔍 Search box
# search_term = st.sidebar.text_input("Search queries...")

# # Drawer-style categories
# categories = get_categories()
# for cat in categories:
#     with st.sidebar.expander(str(cat), expanded=False):  # ensure label is string
#         queries = get_queries(cat)

#         # Filter by search
#         if search_term:
#             queries = [q for q in queries if search_term.lower() in q.lower()]

#         for q in queries:
#             safe_key = f"{str(cat)}_{q}"
#             if st.button(q, key=safe_key):
#                 st.session_state.selected_query = q
#                 st.session_state.df = None  # reset old data

# # ---- MAIN AREA ----
# if st.session_state.selected_query:
#     qname = st.session_state.selected_query
#     st.subheader(f"📝 Query: {qname}")
#     qstring = get_query_text(qname)

#     if not qstring:
#         st.error("Query not found.")
#     else:
#         st.code(qstring, language="sql")

#         # Params
#         params = extract_params(qstring)
#         param_values = []
#         if params:
#             st.info("Enter parameter values:")
#             for p in params:
#                 val = st.text_input(p, "")
#                 param_values.append(val)

#         if st.button("▶ Run Query"):
#             try:
#                 fixed_params = normalize_params(param_values)
#                 df = execute_query(qstring, fixed_params)
#                 st.session_state.df = df
#             except Exception as e:
#                 st.error(f"Error: {e}")

# # ---- RESULTS ----
# if st.session_state.df is not None:
#     df = st.session_state.df
#     if df.empty:
#         st.warning("No results found.")
#     else:
#         st.success(f"Returned {len(df)} rows")

#         view = st.radio(
#             "View as:",
#             ["📋 Table", "📊 Chart"],
#             index=["📋 Table", "📊 Chart"].index(st.session_state.view_mode),
#             key="view_mode"
#         )

#         if view == "📋 Table":
#             st.dataframe(df)
#             csv = df.to_csv(index=False).encode("utf-8")
#             st.download_button("⬇ Download CSV", csv, "data.csv", "text/csv")

#         elif view == "📊 Chart":
#             st.info("Select columns and chart type:")
#             numeric_cols = df.select_dtypes(include="number").columns.tolist()
#             all_cols = df.columns.tolist()

#             chart_type = st.selectbox("Chart Type", ["Bar", "Pie", "Scatter", "Line"])
#             fig = None

#             if chart_type == "Pie":
#                 label_col = st.selectbox("Label Column", all_cols, key="pie_label")
#                 value_col = st.selectbox("Value Column", numeric_cols, key="pie_value")
#                 if label_col and value_col:
#                     fig = px.pie(df, names=label_col, values=value_col)

#             else:
#                 x_col = st.selectbox("X-axis", all_cols, key="x_axis")
#                 y_col = st.selectbox("Y-axis", numeric_cols, key="y_axis")
#                 if x_col and y_col:
#                     if chart_type == "Bar":
#                         fig = px.bar(df, x=x_col, y=y_col)
#                     elif chart_type == "Scatter":
#                         fig = px.scatter(df, x=x_col, y=y_col)
#                     elif chart_type == "Line":
#                         fig = px.line(df, x=x_col, y=y_col)

#             if fig:
#                 st.plotly_chart(fig, use_container_width=True)



# import os
# import re
# import pyodbc
# import pandas as pd
# import streamlit as st
# import plotly.express as px
# from dotenv import load_dotenv
# from datetime import datetime

# # ========== CONFIG ==========
# load_dotenv()

# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_SERVER = os.getenv("DB_SERVER")
# DB_DATABASE = os.getenv("DB_DATABASE")

# LOGIN_USER = os.getenv("LOGIN_USER")
# LOGIN_PASS = os.getenv("LOGIN_PASS")


# # ========== DB CONNECTION ==========
# def get_connection():
#     conn_str = (
#         f"DRIVER={{ODBC Driver 17 for SQL Server}};"
#         f"SERVER={DB_SERVER};DATABASE={DB_DATABASE};"
#         f"UID={DB_USER};PWD={DB_PASSWORD}"
#     )
#     return pyodbc.connect(conn_str)


# # ========== HELPERS ==========
# def get_categories():
#     """Fetch categories with human-readable CatName from OQCN"""
#     with get_connection() as conn:
#         df = pd.read_sql("""
#             SELECT DISTINCT 
#                    OQCN.CategoryId, 
#                    OQCN.CatName
#             FROM OUQR
#             INNER JOIN OQCN ON OUQR.QCategory = OQCN.CategoryId
#             ORDER BY OQCN.CatName
#         """, conn)
#     return df.to_dict("records")   # list of dicts: {CategoryId, CatName}


# def get_queries(category_id):
#     with get_connection() as conn:
#         df = pd.read_sql(
#             "SELECT DISTINCT QName FROM OUQR WHERE QCategory = ?",
#             conn, params=[category_id]
#         )
#     return df["QName"].tolist()


# def get_query_text(qname):
#     with get_connection() as conn:
#         df = pd.read_sql(
#             "SELECT QString FROM OUQR WHERE QName = ?", conn, params=[qname]
#         )
#     if df.empty:
#         return None
#     return df["QString"].iloc[0]


# def execute_query(qstring, params):
#     final_query = re.sub(r"\[%\d+\]", "?", qstring)
#     final_query = re.sub(r"'\?'", "?", final_query)

#     wrapped = f"SET NOCOUNT ON;\n{final_query}"
#     with get_connection() as conn:
#         df = pd.read_sql(wrapped, conn, params=params if params else None)
#     return df


# def extract_params(qstring):
#     matches = re.findall(r"\[%(\d+)\]", qstring)
#     return [f"param{m}" for m in matches]


# def normalize_params(param_values):
#     fixed_params = []
#     for val in param_values:
#         if isinstance(val, datetime):
#             fixed_params.append(val.strftime("%Y-%m-%d"))
#         else:
#             try:
#                 parsed = datetime.strptime(str(val), "%d/%m/%Y")
#                 fixed_params.append(parsed.strftime("%Y-%m-%d"))
#             except Exception:
#                 fixed_params.append(val)
#     return fixed_params


# # ========== STREAMLIT APP ==========
# st.set_page_config("Query Explorer", "📊", layout="wide")

# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False
# if "df" not in st.session_state:
#     st.session_state.df = None
# if "view_mode" not in st.session_state:
#     st.session_state.view_mode = "📋 Table"

# # ---- LOGIN ----
# if not st.session_state.logged_in:
#     st.title("🔐 Login")
#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")
#     if st.button("Login"):
#         if username == LOGIN_USER and password == LOGIN_PASS:
#             st.session_state.logged_in = True
#             st.experimental_rerun()
#         else:
#             st.error("Invalid username or password")
#     st.stop()

# # ---- SIDEBAR ----
# st.sidebar.title("📂 Query Manager SAP B1")
# # st.sidebar.write("Logged in as:", LOGIN_USER)
# if st.sidebar.button("🚪 Logout"):
#     st.session_state.logged_in = False
#     st.experimental_rerun()

# # Search bar
# search_term = st.sidebar.text_input("🔎 Search queries")

# # ---- MAIN LOGIC ----
# categories = get_categories()
# for cat in categories:
#     cat_id = cat["CategoryId"]
#     cat_name = cat["CatName"]

#     with st.sidebar.expander(cat_name, expanded=False):
#         queries = get_queries(cat_id)

#         # Apply search filter
#         if search_term:
#             queries = [q for q in queries if search_term.lower() in q.lower()]

#         for q in queries:
#             safe_key = f"{cat_id}_{q}"
#             if st.button(q, key=safe_key):
#                 st.session_state.selected_query = q
#                 st.session_state.df = None

# # ---- DISPLAY QUERY ----
# if "selected_query" in st.session_state and st.session_state.selected_query:
#     qname = st.session_state.selected_query
#     st.subheader(f"📝 Query: {qname}")
#     qstring = get_query_text(qname)

#     if not qstring:
#         st.error("Query not found.")
#     else:
#         st.code(qstring, language="sql")

#         # Params detection
#         params = extract_params(qstring)
#         param_values = []
#         if params:
#             st.info("Enter parameter values:")
#             for p in params:
#                 if "date" in qstring.lower():
#                     val = st.date_input(p)
#                     param_values.append(val)
#                 else:
#                     val = st.text_input(p, "")
#                     param_values.append(val)

#         # Run button
#         if st.button("▶ Run Query"):
#             try:
#                 fixed_params = normalize_params(param_values)
#                 df = execute_query(qstring, fixed_params)
#                 st.session_state.df = df
#             except Exception as e:
#                 st.error(f"Error: {e}")

# # ---- DISPLAY RESULTS ----
# if st.session_state.df is not None:
#     df = st.session_state.df

#     if df.empty:
#         st.warning("No results found.")
#     else:
#         st.success(f"Returned {len(df)} rows")

#         # Persist view selection
#         view = st.radio(
#             "View as:",
#             ["📋 Table", "📊 Chart"],
#             index=["📋 Table", "📊 Chart"].index(st.session_state.view_mode),
#             key="view_mode"
#         )

#         # ===== TABLE VIEW =====
#         if view == "📋 Table":
#             st.dataframe(df)

#             csv = df.to_csv(index=False).encode("utf-8")
#             st.download_button(
#                 "⬇ Download CSV", csv, "data.csv", "text/csv"
#             )

#         # ===== CHART VIEW =====
#         elif view == "📊 Chart":
#             st.info("Select columns and chart type:")

#             numeric_cols = df.select_dtypes(include="number").columns.tolist()
#             all_cols = df.columns.tolist()

#             chart_type = st.selectbox("Chart Type", ["Bar", "Pie", "Scatter", "Line"])

#             fig = None
#             if chart_type == "Pie":
#                 label_col = st.selectbox("Label Column", all_cols, key="pie_label")
#                 value_col = st.selectbox("Value Column (numeric)", numeric_cols, key="pie_value")

#                 if label_col and value_col:
#                     fig = px.pie(df, names=label_col, values=value_col)

#             elif chart_type in ["Bar", "Scatter", "Line"]:
#                 x_col = st.selectbox("X-axis", all_cols, index=0, key="x_axis")
#                 y_col = st.selectbox("Y-axis (numeric)", numeric_cols, key="y_axis")

#                 if x_col and y_col:
#                     if chart_type == "Bar":
#                         fig = px.bar(df, x=x_col, y=y_col)
#                     elif chart_type == "Scatter":
#                         fig = px.scatter(df, x=x_col, y=y_col)
#                     elif chart_type == "Line":
#                         fig = px.line(df, x=x_col, y=y_col)

#             if fig:
#                 st.plotly_chart(fig, use_container_width=True)
#             else:
#                 st.warning("Please select valid columns for the chart.")




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


# ========== DB CONNECTION ==========
def get_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};DATABASE={DB_DATABASE};"
        f"UID={DB_USER};PWD={DB_PASSWORD}"
    )
    return pyodbc.connect(conn_str)


# ========== HELPERS ==========
def get_categories():
    """Fetch categories with human-readable CatName from OQCN"""
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
            "SELECT QString FROM OUQR WHERE QName = ?", conn, params=[qname]
        )
    if df.empty:
        return None
    return df["QString"].iloc[0]


def execute_query(qstring, params):
    final_query = re.sub(r"\[%\d+\]", "?", qstring)
    final_query = re.sub(r"'\?'", "?", final_query)

    wrapped = f"SET NOCOUNT ON;\n{final_query}"
    with get_connection() as conn:
        df = pd.read_sql(wrapped, conn, params=params if params else None)
    return df


def extract_params(qstring):
    """
    Extract placeholders [%1], [%2] etc. from query and try to give them friendly names
    based on surrounding SQL text.
    """
    mapping = {}
    lines = qstring.splitlines()

    for line in lines:
        match = re.search(r"\[%(\d+)\]", line)
        if match:
            idx = match.group(1)
            label = f"Parameter {idx}"  # default
            line_lower = line.lower()

            if "fromdate" in line_lower or "u_date" in line_lower:
                label = "From Date"
            elif "todate" in line_lower or "u_todate" in line_lower:
                label = "To Date"
            elif "fromcard" in line_lower:
                label = "From Customer"
            elif "tocard" in line_lower:
                label = "To Customer"
            elif "fromlocation" in line_lower:
                label = "From Location"
            elif "tolocation" in line_lower:
                label = "To Location"
            elif "gst" in line_lower:
                label = "GSTIN"
            elif "customer" in line_lower:
                label = "Customer"
            elif "vendor" in line_lower or "supplier" in line_lower:
                label = "Vendor"
            elif "item" in line_lower or "product" in line_lower:
                label = "Item"

            mapping[idx] = label

    # Sort by number
    return [(f"[%{k}]", v) for k, v in sorted(mapping.items(), key=lambda x: int(x[0]))]


def normalize_params(param_values):
    fixed_params = []
    for val in param_values:
        if isinstance(val, datetime):
            fixed_params.append(val.strftime("%Y-%m-%d"))
        else:
            try:
                parsed = datetime.strptime(str(val), "%d/%m/%Y")
                fixed_params.append(parsed.strftime("%Y-%m-%d"))
            except Exception:
                fixed_params.append(val)
    return fixed_params


# ========== STREAMLIT APP ==========
st.set_page_config("Query Explorer", "📊", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "df" not in st.session_state:
    st.session_state.df = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "📋 Table"

# ---- LOGIN ----
if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == LOGIN_USER and password == LOGIN_PASS:
            st.session_state.logged_in = True
            # st.experimental_rerun()
            st.rerun()
        else:
            st.error("Invalid username or password")
    st.stop()

# ---- SIDEBAR ----
st.sidebar.title("📂 Query Manager SAP B1")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.experimental_rerun()

# Search bar
search_term = st.sidebar.text_input("🔎 Search queries")

# ---- MAIN LOGIC ----
categories = get_categories()
for cat in categories:
    cat_id = cat["CategoryId"]
    cat_name = cat["CatName"]

    with st.sidebar.expander(cat_name, expanded=False):
        queries = get_queries(cat_id)
        if search_term:
            queries = [q for q in queries if search_term.lower() in q.lower()]

        for q in queries:
            safe_key = f"{cat_id}_{q}"
            if st.button(q, key=safe_key):
                st.session_state.selected_query = q
                st.session_state.df = None

# ---- DISPLAY QUERY ----
if "selected_query" in st.session_state and st.session_state.selected_query:
    qname = st.session_state.selected_query
    st.subheader(f"📝 Query: {qname}")
    qstring = get_query_text(qname)

    if not qstring:
        st.error("Query not found.")
    else:
        st.code(qstring, language="sql")

        # Params detection
        params = extract_params(qstring)
        param_values = []
        if params:
            st.info("Enter parameter values:")
            for placeholder, label in params:
                if "Date" in label:
                    val = st.date_input(label)
                else:
                    val = st.text_input(label, "")
                param_values.append(val)

        # Run button
        if st.button("▶ Run Query"):
            try:
                fixed_params = normalize_params(param_values)
                df = execute_query(qstring, fixed_params)
                st.session_state.df = df
            except Exception as e:
                st.error(f"Error: {e}")

# ---- DISPLAY RESULTS ----
if st.session_state.df is not None:
    df = st.session_state.df

    if df.empty:
        st.warning("No results found.")
    else:
        st.success(f"Returned {len(df)} rows")

        view = st.radio(
            "View as:",
            ["📋 Table", "📊 Chart"],
            index=["📋 Table", "📊 Chart"].index(st.session_state.view_mode),
            key="view_mode"
        )

        if view == "📋 Table":
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Download CSV", csv, "data.csv", "text/csv")

        elif view == "📊 Chart":
            st.info("Select columns and chart type:")
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            all_cols = df.columns.tolist()

            chart_type = st.selectbox("Chart Type", ["Bar", "Pie", "Scatter", "Line"])
            fig = None

            if chart_type == "Pie":
                label_col = st.selectbox("Label Column", all_cols, key="pie_label")
                value_col = st.selectbox("Value Column (numeric)", numeric_cols, key="pie_value")
                if label_col and value_col:
                    fig = px.pie(df, names=label_col, values=value_col)

            elif chart_type in ["Bar", "Scatter", "Line"]:
                x_col = st.selectbox("X-axis", all_cols, index=0, key="x_axis")
                y_col = st.selectbox("Y-axis (numeric)", numeric_cols, key="y_axis")
                if x_col and y_col:
                    if chart_type == "Bar":
                        fig = px.bar(df, x=x_col, y=y_col)
                    elif chart_type == "Scatter":
                        fig = px.scatter(df, x=x_col, y=y_col)
                    elif chart_type == "Line":
                        fig = px.line(df, x=x_col, y=y_col)

            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Please select valid columns for the chart.")

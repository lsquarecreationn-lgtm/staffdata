# streamlit_app.py
import streamlit as st
import pandas as pd
import os
from io import BytesIO
from datetime import datetime

# ------------------------
# Config / paths
# ------------------------
BASE_DIR = r"D:\IIS\staffdata"
os.makedirs(BASE_DIR, exist_ok=True)
MASTER_PATH = os.path.join(BASE_DIR, "master.xlsx")
SUBMISSIONS_PATH = os.path.join(BASE_DIR, "submissions.xlsx")

ADMIN_PASSWORD = "admin@9852"

MASTER_HEADERS = ["Emp. No.", "NAME"]
SUBMIT_HEADERS = [
    "Emp. No.", "NAME", "Mobile", "Email",
    "Highest Academic Qualification",
    "Highest Professional Qualification",
    "Section", "Submitted At"
]

ACADEMIC_Q = [
    "Ph.D.", "M.Phil.", "M.A.", "M.Sc.", "M.Com.", "M.Ed.", "MBA", "MCA", "M.Tech",
    "B.A.", "B.Sc.", "B.Com.", "B.Ed.", "BBA", "BCA", "B.Tech", "B.E.",
    "Diploma", "PG Diploma", "Inter/PUC (+2)", "SSLC/10th"
]
PROF_Q = [
    "B.Ed.", "M.Ed.", "B.P.Ed.", "M.P.Ed.", "D.El.Ed.", "D.Ed.",
    "TTC", "NTT", "SET", "NET", "CTET", "STET", "M.Phil.", "Ph.D."
]
SECTIONS = [
    "Boys Section (Morning)", "Boys Section (Evening)",
    "Girls Section (Morning)", "Girls Section (Evening)",
    "Junior Section (Morning)", "Junior Section (Evening)",
    "KG Section (Morning)", "KG Section (Evening)"
]

st.set_page_config(page_title="IIS Staff Data • OASIS", layout="wide")

# ------------------------
# Helpers
# ------------------------
def load_master_from_disk():
    if os.path.exists(MASTER_PATH):
        try:
            df = pd.read_excel(MASTER_PATH, dtype=str)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception:
            return pd.DataFrame(columns=MASTER_HEADERS)
    return pd.DataFrame(columns=MASTER_HEADERS)

def save_master_to_disk(uploaded_bytes):
    # uploaded_bytes: bytes
    with open(MASTER_PATH, "wb") as f:
        f.write(uploaded_bytes)

def load_submissions_from_disk():
    if os.path.exists(SUBMISSIONS_PATH):
        try:
            df = pd.read_excel(SUBMISSIONS_PATH, dtype=str)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception:
            return pd.DataFrame(columns=SUBMIT_HEADERS)
    return pd.DataFrame(columns=SUBMIT_HEADERS)

def save_submissions_to_disk(df):
    df.to_excel(SUBMISSIONS_PATH, index=False)

def to_excel_bytes(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return out.getvalue()

# ------------------------
# Load persisted data on startup
# ------------------------
master_df = load_master_from_disk()
submissions_df = load_submissions_from_disk()

# session state initial values
if "mode" not in st.session_state:
    st.session_state.mode = "User"
if "verified_emp" not in st.session_state:
    st.session_state.verified_emp = ""
if "verified_name" not in st.session_state:
    st.session_state.verified_name = ""
if "step" not in st.session_state:
    st.session_state.step = 1

# ------------------------
# Sidebar: mode (User / Admin)
# ------------------------
st.sidebar.title("Mode")
mode = st.sidebar.radio("", ["User", "Admin"], index=0)
st.session_state.mode = mode

# ------------------------
# ADMIN
# ------------------------
if mode == "Admin":
    st.header("🔒 Admin Panel")
    pwd = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
    if pwd != ADMIN_PASSWORD:
        st.info("Enter correct admin password to continue.")
        st.stop()

    st.success("Admin authenticated")

    st.subheader("1) Upload / Replace Master Staff Excel")
    st.caption("Required columns: 'Emp. No.' and 'NAME' (case-insensitive). This file will be saved to disk and used by user verification.")
    uploaded = st.file_uploader("Upload master Excel (.xlsx)", type=["xlsx"], help="Upload 'master' Excel with Emp. No. and NAME")
    if uploaded is not None:
        bytes_data = uploaded.getvalue()
        try:
            tmp = pd.read_excel(BytesIO(bytes_data), dtype=str)
            # simple normalization
            tmp.rename(columns=lambda c: c.strip(), inplace=True)
            # try to map possible header variants
            cols = {c: c for c in tmp.columns}
            for c in tmp.columns:
                lc = c.lower().strip()
                if lc in ["emp no", "emp. no.", "emp_no", "empno", "emp. no"]:
                    cols[c] = "Emp. No."
                if lc in ["name", "full name", "employee name", "name - pls remember this", "name - pls remember this"]:
                    cols[c] = "NAME"
            tmp.rename(columns=cols, inplace=True)
            if not set(MASTER_HEADERS).issubset(tmp.columns):
                st.error(f"Missing required headers. Found: {list(tmp.columns)}. Required: {MASTER_HEADERS}")
            else:
                save_master_to_disk(bytes_data)
                master_df = load_master_from_disk()
                st.success(f"Master saved to disk: {MASTER_PATH}")
                st.dataframe(master_df[MASTER_HEADERS], height=300, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to read uploaded file: {e}")

    st.divider()
    st.subheader("2) View & Export Submissions")
    st.write(f"Submissions on disk: **{len(submissions_df)}**")
    st.dataframe(submissions_df, height=300, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if len(submissions_df) > 0:
            st.download_button("⬇ Download Submissions (Excel)", to_excel_bytes(submissions_df), file_name="submissions.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.button("⬇ Download Submissions (Excel)", disabled=True)
    with col2:
        not_sub = pd.DataFrame(columns=MASTER_HEADERS)
        if not master_df.empty:
            not_sub = master_df[~master_df["Emp. No."].astype(str).isin(submissions_df["Emp. No."].astype(str))]
        if len(not_sub) > 0:
            st.download_button("⬇ Download NOT Submitted", to_excel_bytes(not_sub), file_name="not_submitted.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.button("⬇ Download NOT Submitted", disabled=True)
    with col3:
        if st.button("🗑 Clear submissions (delete file)"):
            if os.path.exists(SUBMISSIONS_PATH):
                os.remove(SUBMISSIONS_PATH)
            submissions_df = pd.DataFrame(columns=SUBMIT_HEADERS)
            st.success("Submissions file deleted. Session cleared.")
            # refresh local variable
            submissions_df = load_submissions_from_disk()

    st.info(f"Master file path: {MASTER_PATH}")
    st.info(f"Submissions file path: {SUBMISSIONS_PATH}")
    st.caption("Note: keep server machine / D: drive backed up regularly. Streamlit Cloud ephemeral filesystem loses files on redeploys; running locally on your PC keeps files persistent.")

# ------------------------
# USER
# ------------------------
else:
    st.header("👤 Staff Self-Entry Portal (User)")
    st.write("Step 1 — enter Employee Number; we will verify name from master list saved by Admin.")

    # ensure master is present:
    master_df = load_master_from_disk()
    if master_df.empty:
        st.warning("Admin has not uploaded the master list (or it's missing on disk). Please ask Admin to upload in Admin mode.")
        st.stop()

    # normalize columns
    master_df.rename(columns=lambda c: c.strip(), inplace=True)
    # map common name variants to expected
    cols_map = {}
    for c in master_df.columns:
        lc = c.lower().strip()
        if lc in ["emp no", "emp. no.", "emp_no", "empno"]:
            cols_map[c] = "Emp. No."
        if lc in ["name", "full name", "employee name"]:
            cols_map[c] = "NAME"
    master_df.rename(columns=cols_map, inplace=True)

    if not set(MASTER_HEADERS).issubset(master_df.columns):
        st.error("Master list does not contain required columns 'Emp. No.' and 'NAME'. Ask Admin to re-upload.")
        st.stop()

    # Step 1: verify
    step = st.session_state.get("step", 1)
    if step == 1:
        emp = st.text_input("Employee Number", placeholder="Type your Emp. No. here")
        if st.button("Verify"):
            if not emp:
                st.error("Enter an Employee Number.")
            else:
                matched = master_df[master_df["Emp. No."].astype(str).str.strip() == str(emp).strip()]
                if matched.empty:
                    st.error("Employee Number not found. Contact Admin.")
                else:
                    st.session_state.verified_emp = str(emp).strip()
                    st.session_state.verified_name = str(matched.iloc[0]["NAME"])
                    st.session_state.step = 2
                    st.experimental_rerun()  # safe when running locally; if your Streamlit version lacks it, next run will still work

    # Step 2: confirm name
    elif step == 2:
        st.success("Employee number found.")
        st.write("Employee Number:", st.session_state.verified_emp)
        st.write("Name:", st.session_state.verified_name)
        c1, c2 = st.columns(2)
        if c1.button("Confirm"):
            st.session_state.step = 3
            st.experimental_rerun()
        if c2.button("Change number"):
            st.session_state.verified_emp = ""
            st.session_state.verified_name = ""
            st.session_state.step = 1
            st.experimental_rerun()

    # Step 3: form
    elif step == 3:
        emp_no = st.session_state.verified_emp
        emp_name = st.session_state.verified_name

        # reload submissions to be safe
        submissions_df = load_submissions_from_disk()

        if not submissions_df[submissions_df["Emp. No."].astype(str) == str(emp_no)].empty:
            st.warning("This Employee Number has already submitted the form. Duplicate prevented.")
            if st.button("Start over"):
                st.session_state.step = 1
                st.session_state.verified_emp = ""
                st.session_state.verified_name = ""
                st.experimental_rerun()
            st.stop()

        st.subheader("Form — Staff Qualification Details")
        st.write(f"**Employee:** {emp_no} — {emp_name}")

        with st.form("qual_form", clear_on_submit=False):
            mobile = st.text_input("Mobile Number", placeholder="e.g., 55512345")
            email = st.text_input("Email", placeholder="name@example.com")
            col1, col2 = st.columns(2)
            with col1:
                acad = st.selectbox("Highest Academic Qualification", options=ACADEMIC_Q, index=2)
            with col2:
                prof = st.selectbox("Highest Professional Qualification", options=PROF_Q, index=0)
            section = st.selectbox("Section", options=SECTIONS)
            submitted = st.form_submit_button("Submit")

            if submitted:
                # add to submissions_df and save to disk
                rec = {
                    "Emp. No.": str(emp_no),
                    "NAME": str(emp_name),
                    "Mobile": mobile.strip(),
                    "Email": email.strip(),
                    "Highest Academic Qualification": acad,
                    "Highest Professional Qualification": prof,
                    "Section": section,
                    "Submitted At": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                }
                submissions_df = pd.concat([submissions_df, pd.DataFrame([rec])], ignore_index=True)
                try:
                    save_submissions_to_disk(submissions_df)
                    st.success("✅ Submitted and saved to server disk. Thank you!")
                except Exception as e:
                    st.error(f"Saved to session but failed to write file: {e}")
                # reset steps
                st.session_state.step = 4

    # Step 4: done
    elif step == 4:
        st.success("Submission recorded.")
        if st.button("Submit another"):
            st.session_state.step = 1
            st.session_state.verified_emp = ""
            st.session_state.verified_name = ""
            st.experimental_rerun()


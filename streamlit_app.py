# streamlit_app.py
import streamlit as st
import pandas as pd
import os
from io import BytesIO

# -------------------------
# Configuration / paths
# -------------------------
ADMIN_PASSWORD = "admin@9852"
BASE_DIR = r"D:\IIS\staffdata"
os.makedirs(BASE_DIR, exist_ok=True)
MASTER_PATH = os.path.join(BASE_DIR, "master.xlsx")          # saved master list here
SUBMISSIONS_PATH = os.path.join(BASE_DIR, "submissions.xlsx")# saved submissions here

MASTER_HEADERS = ["Emp. No.", "NAME"]
SUBMIT_HEADERS = ["Emp. No.", "NAME", "Mobile", "Email",
                  "Highest Academic Qualification",
                  "Highest Professional Qualification",
                  "Section", "Submitted At"]

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

# -------------------------
# Helpers: load/save
# -------------------------
@st.cache_data(show_spinner=False)
def load_master_from_disk() -> pd.DataFrame:
    if os.path.exists(MASTER_PATH):
        try:
            df = pd.read_excel(MASTER_PATH, dtype=str)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception:
            return pd.DataFrame(columns=MASTER_HEADERS)
    return pd.DataFrame(columns=MASTER_HEADERS)

def save_master_to_disk(df: pd.DataFrame):
    df.to_excel(MASTER_PATH, index=False)

def load_submissions_from_disk() -> pd.DataFrame:
    if os.path.exists(SUBMISSIONS_PATH):
        try:
            df = pd.read_excel(SUBMISSIONS_PATH, dtype=str)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception:
            return pd.DataFrame(columns=SUBMIT_HEADERS)
    return pd.DataFrame(columns=SUBMIT_HEADERS)

def save_submissions_to_disk(df: pd.DataFrame):
    df.to_excel(SUBMISSIONS_PATH, index=False)

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return out.getvalue()

# -------------------------
# Initialize session state
# -------------------------
if "submissions" not in st.session_state:
    st.session_state["submissions"] = load_submissions_from_disk()
if "master_df" not in st.session_state:
    st.session_state["master_df"] = load_master_from_disk()
if "user_step" not in st.session_state:
    st.session_state["user_step"] = 1

# -------------------------
# UI
# -------------------------
st.set_page_config(page_title="IIS Staff Data • OASIS", layout="wide")
mode = st.sidebar.radio("Mode", ["User", "Admin"], index=0)
st.sidebar.caption("Default is User. Admin requires password.")

# -------------------------
# ADMIN
# -------------------------
if mode == "Admin":
    st.header("🔐 Admin")
    pwd = st.text_input("Admin password", type="password")
    if pwd != ADMIN_PASSWORD:
        st.info("Enter admin password to continue.")
        st.stop()

    st.success("Admin authenticated")
    st.subheader("Upload Master Staff Excel (Emp. No., NAME)")
    st.caption("This master file will be saved to the server at: " + MASTER_PATH)

    uploaded = st.file_uploader("Upload master .xlsx (required headers: Emp. No., NAME)", type=["xlsx"])
    if uploaded is not None:
        # read and normalize
        try:
            df = pd.read_excel(uploaded, dtype=str)
            df.columns = [c.strip() for c in df.columns]
            # map common variations
            cols = {c: c for c in df.columns}
            for c in df.columns:
                lc = c.lower().strip()
                if lc in ["emp no", "emp. no.", "emp_no", "empno", "emp. no"]:
                    cols[c] = "Emp. No."
                if lc in ["name", "full name", "employee name"]:
                    cols[c] = "NAME"
            df = df.rename(columns=cols)
            missing = [h for h in MASTER_HEADERS if h not in df.columns]
            if missing:
                st.error(f"Missing required headers: {missing}. File not saved.")
            else:
                st.session_state["master_df"] = df
                save_master_to_disk(df)
                st.success("Master saved to disk.")
                st.dataframe(df[MASTER_HEADERS], use_container_width=True, height=300)
        except Exception as e:
            st.error("Failed to read Excel: " + str(e))

    st.divider()
    st.subheader("Submissions")
    subdf = st.session_state["submissions"]
    st.write(f"Total submissions: {len(subdf)}")
    st.dataframe(subdf, use_container_width=True, height=300)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("Download Submissions (xlsx)", data=to_excel_bytes(subdf),
                           file_name="submissions.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        # not submitted
        master_df = st.session_state["master_df"]
        if not master_df.empty:
            not_sub = master_df[~master_df["Emp. No."].astype(str).isin(subdf["Emp. No."].astype(str))]
            st.download_button("Download NOT Submitted", data=to_excel_bytes(not_sub),
                               file_name="not_submitted.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.button("Download NOT Submitted", disabled=True)

    with c3:
        if st.button("Clear submissions (delete file on disk)"):
            st.session_state["submissions"] = pd.DataFrame(columns=SUBMIT_HEADERS)
            if os.path.exists(SUBMISSIONS_PATH):
                os.remove(SUBMISSIONS_PATH)
            st.success("Submissions cleared.")
            # refresh view
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()

    st.info("Notes: Uploaded master and submissions are stored in the folder on this machine. If you restart the machine, the files remain on disk (D:\\IIS\\staffdata) unless you remove them.")

# -------------------------
# USER
# -------------------------
else:
    st.header("👤 Staff Self-Entry (User)")
    st.caption("Step 1: Enter Employee Number (Emp. No.) — we will verify your name from the uploaded master list.")

    master_df = st.session_state.get("master_df", pd.DataFrame(columns=MASTER_HEADERS))
    if master_df.empty:
        st.warning("Admin hasn't uploaded the master staff list in this running instance. Ask Admin to upload (Admin → upload).")
        st.stop()

    step = st.session_state.get("user_step", 1)

    if step == 1:
        emp_no = st.text_input("Employee Number (Emp. No.)", key="inp_emp_no")
        if st.button("Verify"):
            if not emp_no:
                st.error("Type an employee number then press Verify.")
            else:
                row = master_df[master_df["Emp. No."].astype(str).str.strip() == str(emp_no).strip()]
                if row.empty:
                    st.error("Employee number not found. Check with Admin.")
                else:
                    st.session_state["emp_no"] = str(emp_no).strip()
                    st.session_state["emp_name"] = str(row.iloc[0]["NAME"])
                    st.session_state["user_step"] = 2
                    if hasattr(st, "experimental_rerun"):
                        st.experimental_rerun()

    elif step == 2:
        st.success("Employee found.")
        st.metric("Employee Number", st.session_state.get("emp_no", ""))
        st.metric("Name", st.session_state.get("emp_name", ""))
        col1, col2 = st.columns(2)
        if col1.button("Confirm"):
            st.session_state["user_step"] = 3
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()
        if col2.button("Change number"):
            st.session_state["user_step"] = 1
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()

    elif step == 3:
        emp_no = st.session_state.get("emp_no")
        emp_name = st.session_state.get("emp_name")
        subdf = st.session_state["submissions"]

        # duplicate check
        if not subdf[subdf["Emp. No."].astype(str) == str(emp_no)].empty:
            st.warning("Your entry already exists. Duplicate submissions are not allowed.")
            st.stop()

        st.subheader("Form: Qualification & Contact")
        st.write(f"**Employee:** {emp_no} — {emp_name}")
        mobile = st.text_input("Mobile Number", placeholder="e.g., 5XXXXXXXX")
        email = st.text_input("Email", placeholder="name@example.com")
        col1, col2 = st.columns(2)
        with col1:
            acad = st.selectbox("Highest Academic Qualification", ACADEMIC_Q, index=ACADEMIC_Q.index("M.A.") if "M.A." in ACADEMIC_Q else 0)
        with col2:
            prof = st.selectbox("Highest Professional Qualification", PROF_Q, index=0)
        section = st.selectbox("Section", SECTIONS)

        if st.button("Submit"):
            rec = {
                "Emp. No.": str(emp_no),
                "NAME": str(emp_name),
                "Mobile": str(mobile).strip(),
                "Email": str(email).strip(),
                "Highest Academic Qualification": acad,
                "Highest Professional Qualification": prof,
                "Section": section,
                "Submitted At": pd.Timestamp.now(tz='UTC').strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            st.session_state["submissions"] = pd.concat([subdf, pd.DataFrame([rec])], ignore_index=True)
            save_submissions_to_disk(st.session_state["submissions"])
            st.success("Submitted — thank you!")
            st.balloons()
            st.session_state["user_step"] = 4
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()

    elif step == 4:
        st.success("Your response is recorded.")
        if st.button("Submit another"):
            st.session_state["user_step"] = 1
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()

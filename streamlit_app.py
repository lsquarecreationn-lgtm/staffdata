import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="IIS Staff Data • OASIS", layout="wide")

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

# Session variables
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "user_step" not in st.session_state:
    st.session_state.user_step = 1
if "submissions" not in st.session_state:
    st.session_state.submissions = pd.DataFrame(columns=SUBMIT_HEADERS)

@st.cache_data(show_spinner=False)
def load_master(upload_bytes):
    if upload_bytes is None:
        return pd.DataFrame(columns=MASTER_HEADERS)
    df = pd.read_excel(upload_bytes, dtype=str)
    df.columns = df.columns.str.strip()
    return df

def to_excel(df):
    out = BytesIO()
    df.to_excel(out, index=False)
    return out.getvalue()

mode = st.sidebar.radio("Choose Mode", ["User", "Admin"], index=0)

# ---------------- ADMIN PANEL ----------------
if mode == "Admin":
    st.header("🔐 Admin Login")

    if not st.session_state.admin_logged_in:
        pwd = st.text_input("Enter Admin Password", type="password")

        if st.button("Login"):
            if pwd == "admin@9852":   # Change if needed
                st.session_state.admin_logged_in = True
                st.success("✅ Login Successful")
                st.experimental_rerun()
            else:
                st.error("❌ Incorrect Password")
        st.stop()

    st.success("✅ Admin Access Granted")

    st.subheader("Upload Master Staff List (.xlsx)")
    master_file = st.file_uploader("Upload Excel File", type=["xlsx"])

    if master_file:
        st.session_state.master_upload = master_file

    if st.session_state.get("master_upload") is not None:
        master_df = load_master(st.session_state.master_upload.getvalue())

        rename_map = {}
        for c in master_df.columns:
            lc = c.lower().strip()
            if lc.startswith("emp"):
                rename_map[c] = "Emp. No."
            if "name" in lc:
                rename_map[c] = "NAME"
        master_df = master_df.rename(columns=rename_map)

        if set(MASTER_HEADERS).issubset(master_df.columns):
            st.dataframe(master_df[MASTER_HEADERS], use_container_width=True)
        else:
            st.error("Excel must contain **Emp. No.** and **NAME** columns.")

    st.divider()
    st.subheader("Submitted Records")
    st.dataframe(st.session_state.submissions, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button("⬇️ Download Submitted", to_excel(st.session_state.submissions),
                           "submitted.xlsx")

    with col2:
        if st.session_state.get("master_upload") is not None:
            ns = master_df[~master_df["Emp. No."].isin(st.session_state.submissions["Emp. No."])]
            st.download_button("⬇️ Download Not Submitted", to_excel(ns), "not_submitted.xlsx")

    with col3:
        if st.button("🗑 Clear All Submissions"):
            st.session_state.submissions = pd.DataFrame(columns=SUBMIT_HEADERS)
            st.success("✅ All submissions cleared")

# ---------------- USER PAGE ----------------
else:
    st.header("👤 Staff Self-Entry Form")
    st.caption("Verify your Employee Number first to begin.")
    st.divider()

    if st.session_state.get("master_upload") is None:
        st.warning("⚠️ Admin has not uploaded the staff list yet.")
        st.stop()

    master_df = load_master(st.session_state.master_upload.getvalue())

    rename_map = {}
    for c in master_df.columns:
        lc = c.lower().strip()
        if lc.startswith("emp"):
            rename_map[c] = "Emp. No."
        if "name" in lc:
            rename_map[c] = "NAME"
    master_df = master_df.rename(columns=rename_map)

    # Step 1 – verify employee number
    if st.session_state.user_step == 1:
        emp_no = st.text_input("Enter Your Employee Number:", placeholder="Example: 10025").strip()

        if st.button("Verify"):
            row = master_df[master_df["Emp. No."].astype(str).str.strip() == emp_no]
            if row.empty:
                st.error("❌ Employee Number not found.")
            else:
                st.session_state.emp_no = emp_no
                st.session_state.emp_name = row.iloc[0]["NAME"]
                st.session_state.user_step = 2
                st.experimental_rerun()

    # Step 2 – confirm name
    if st.session_state.user_step == 2:
        st.success("✅ Employee Found")
        st.write(f"**Employee Number:** {st.session_state.emp_no}")
        st.write(f"**Name:** {st.session_state.emp_name}")

        c1, c2 = st.columns(2)
        if c1.button("Confirm ✅"):
            st.session_state.user_step = 3
            st.experimental_rerun()
        if c2.button("Change Number ↩"):
            st.session_state.user_step = 1
            st.experimental_rerun()

    # Step 3 – form
    if st.session_state.user_step == 3:

        if st.session_state.emp_no in st.session_state.submissions["Emp. No."].values:
            st.warning("⚠️ You have already submitted. Duplicate not allowed.")
            st.stop()

        st.subheader("Qualification Form")
        mobile = st.text_input("Mobile Number")
        email = st.text_input("Email Address")
        col1, col2 = st.columns(2)
        academic = col1.selectbox("Highest Academic Qualification", ACADEMIC_Q)
        professional = col2.selectbox("Highest Professional Qualification", PROF_Q)
        section = st.selectbox("Select Section", SECTIONS)

        if st.button("Submit ✅"):
            new_data = {
                "Emp. No.": st.session_state.emp_no,
                "NAME": st.session_state.emp_name,
                "Mobile": mobile,
                "Email": email,
                "Highest Academic Qualification": academic,
                "Highest Professional Qualification": professional,
                "Section": section,
                "Submitted At": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.submissions = pd.concat(
                [st.session_state.submissions, pd.DataFrame([new_data])],
                ignore_index=True
            )
            st.success("✅ Submitted Successfully!")
            st.balloons()
            st.session_state.user_step = 1

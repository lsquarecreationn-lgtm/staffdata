
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="IIS Staff Data • OASIS (Streamlit)", layout="wide")

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

@st.cache_data(show_spinner=False)
def load_master(upload_bytes: bytes) -> pd.DataFrame:
    if upload_bytes is None:
        return pd.DataFrame(columns=MASTER_HEADERS)
    return pd.read_excel(upload_bytes, dtype=str).rename(columns=lambda c: c.strip())

def ensure_submit_df() -> pd.DataFrame:
    if "submissions" not in st.session_state:
        st.session_state["submissions"] = pd.DataFrame(columns=SUBMIT_HEADERS)
    return st.session_state["submissions"]

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

mode = st.sidebar.radio("Choose mode", ["User", "Admin"], index=0)
st.sidebar.caption("Default is **User**. Admin requires password.")

if mode == "Admin":
    st.header("🔐 Admin")
    pwd = st.text_input("Enter Admin Password", type="password", placeholder="••••••")
    if pwd != st.secrets.get("ADMIN_PASSWORD", "admin@9852"):
        st.info("Provide the correct admin password to continue.")
        st.stop()

    st.success("✅ Admin authenticated")
    st.subheader("1) Upload Master Staff List (Excel)")
    st.caption("Required headers: ‘Emp. No.’ and ‘NAME’.")
    master_file = st.file_uploader("Upload master Excel (.xlsx)", type=["xlsx"], key="master_upload")

    master_df = load_master(master_file.getvalue() if master_file else None)
    if not master_df.empty:
        cols = {c: c for c in master_df.columns}
        for c in master_df.columns:
            lc = c.lower().strip()
            if lc in ["emp no", "emp. no.", "emp_no", "empno", "emp. no"]:
                cols[c] = "Emp. No."
            if lc in ["name", "full name", "employee name"]:
                cols[c] = "NAME"
        master_df = master_df.rename(columns=cols)
        missing = [h for h in MASTER_HEADERS if h not in master_df.columns]
        if missing:
            st.error(f"Missing required header(s): {missing}")
        else:
            st.dataframe(master_df[MASTER_HEADERS], use_container_width=True, height=300)

    st.divider()
    st.subheader("2) View / Export Submissions")
    sub_df = ensure_submit_df()
    st.write(f"Total submissions: **{len(sub_df)}**")
    st.dataframe(sub_df, use_container_width=True, height=320)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("⬇️ Download Submissions (Excel)",
                           data=to_excel_bytes(sub_df),
                           file_name="submissions.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        if not master_df.empty and set(MASTER_HEADERS).issubset(master_df.columns):
            not_submitted = master_df[~master_df["Emp. No."].astype(str).isin(sub_df["Emp. No."].astype(str))]
            st.download_button("⬇️ Download NOT Submitted (Excel)",
                               data=to_excel_bytes(not_submitted),
                               file_name="not_submitted.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.button("⬇️ Download NOT Submitted (Excel)", disabled=True)
    with c3:
        if st.button("🗑 Clear submissions (session only)"):
            st.session_state["submissions"] = pd.DataFrame(columns=SUBMIT_HEADERS)
            st.experimental_rerun()

    st.info("Files on Streamlit Cloud are ephemeral. Keep exported copies.")

else:
    st.header("👤 Staff Self‑Entry Portal (User)")
    st.caption("Step‑1: Enter your Employee Number. We will verify your NAME from the master list.")
    st.divider()

    master_file_state = st.session_state.get("master_upload")
    if master_file_state is None:
        st.warning("Admin hasn’t uploaded the Master Staff Excel in this session yet. Please ask Admin to upload it from the Admin tab.")
        st.stop()

    master_df = load_master(master_file_state.getvalue())
    cols = {c: c for c in master_df.columns}
    for c in master_df.columns:
        lc = c.lower().strip()
        if lc in ["emp no", "emp. no.", "emp_no", "empno", "emp. no"]:
            cols[c] = "Emp. No."
        if lc in ["name", "full name", "employee name"]:
            cols[c] = "NAME"
    master_df = master_df.rename(columns=cols)
    missing = [h for h in MASTER_HEADERS if h not in master_df.columns]
    if missing:
        st.error("Master list columns are incorrect. Please ask Admin to re-upload.")
        st.stop()

    sub_df = ensure_submit_df()
    step = st.session_state.get("user_step", 1)

    if step == 1:
        emp_no = st.text_input("Enter your Employee Number", placeholder="e.g., 10025").strip()
        if st.button("Verify"):
            row = master_df[master_df["Emp. No."].astype(str).str.strip() == emp_no]
            if row.empty:
                st.error("Employee number not found. Please check with Admin.")
            else:
                name = row.iloc[0]["NAME"]
                st.session_state["emp_no"] = emp_no
                st.session_state["emp_name"] = str(name)
                st.session_state["user_step"] = 2
                st.experimental_rerun()

    if step == 2:
        st.success("Employee number found in the master list.")
        st.metric("Employee Number", st.session_state.get("emp_no", ""))
        st.metric("Name", st.session_state.get("emp_name", ""))
        st.write("If this is correct, click Confirm to continue.")
        c1, c2 = st.columns(2)
        if c1.button("✅ Confirm"):
            st.session_state["user_step"] = 3
            st.experimental_rerun()
        if c2.button("↩️ Change Number"):
            st.session_state["user_step"] = 1
            st.experimental_rerun()

    if step == 3:
        emp_no = st.session_state.get("emp_no")
        emp_name = st.session_state.get("emp_name")

        if not sub_df[sub_df["Emp. No."].astype(str) == str(emp_no)].empty:
            st.warning("You have already submitted the form. Duplicate entries are not allowed.")
            st.stop()

        st.subheader("Form – Staff Qualification Details")
        st.write(f"**Employee Number:** {emp_no}   |   **Name:** {emp_name}")

        mobile = st.text_input("Mobile Number", placeholder="e.g., 55512345")
        email = st.text_input("Email", placeholder="name@example.com")
        col1, col2 = st.columns(2)
        with col1:
            acad = st.selectbox("Select Highest Academic Qualification", ACADEMIC_Q, index=2)
        with col2:
            prof = st.selectbox("Select Highest Professional Qualification", PROF_Q, index=0)
        section = st.selectbox("Select Section", SECTIONS)

        if st.button("📨 Submit"):
            if not emp_no or not emp_name:
                st.error("Verification missing. Please go back.")
            else:
                rec = {
                    "Emp. No.": str(emp_no),
                    "NAME": str(emp_name),
                    "Mobile": mobile.strip(),
                    "Email": email.strip(),
                    "Highest Academic Qualification": acad,
                    "Highest Professional Qualification": prof,
                    "Section": section,
                    "Submitted At": pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d %H:%M:%S UTC')
                }
                st.session_state["submissions"] = pd.concat([sub_df, pd.DataFrame([rec])], ignore_index=True)
                st.success("✅ Submitted successfully!")
                st.balloons()
                st.session_state["user_step"] = 4
                st.experimental_rerun()

    if step == 4:
        st.success("Your response has been recorded. Thank you!")
        if st.button("Submit another response"):
            st.session_state["user_step"] = 1
            st.experimental_rerun()

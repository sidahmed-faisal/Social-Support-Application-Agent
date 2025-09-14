import streamlit as st
import requests, os
from typing import List

API_URL = os.environ.get("API_Base_URL", "http://localhost:8000")
st.set_page_config(page_title="Social Support AI — Chatbot & Intake", layout="wide")

# ---------------- Sidebar: API config ----------------
st.sidebar.title("⚙️ API Settings")
api_base = st.sidebar.text_input("API Base URL", value=API_URL, help="Root URL where FastAPI is running")
process_url = f"{api_base}/process"
chat_url = f"{api_base}/chat"

st.sidebar.markdown("---")
st.sidebar.caption("This UI calls two endpoints: `/process` and `/chat`.")

# ---------------- Layout ----------------
left_col, right_col = st.columns([1, 2], gap="large")

# ---------------- Left: Intake & Results ----------------
with left_col:
    st.header("📥 Applicant Intake")
    st.write("Upload **exactly four** files:")
    id_file = st.file_uploader("Emirates ID (.png / .jpg / .jpeg)", type=["png", "jpg", "jpeg"], key="id_file")
    assets_file = st.file_uploader("Assets & Liabilities (.xlsx / .xls)", type=["xlsx", "xls"], key="assets_file")
    bank_file = st.file_uploader("Bank Statement (.csv)", type=["csv"], key="bank_file")
    credit_file = st.file_uploader("Credit Report (.pdf)", type=["pdf"], key="credit_file")

    if "decision_status" not in st.session_state:
        st.session_state.decision_status = ""
    if "final_summary" not in st.session_state:
        st.session_state.final_summary = ""
    if "inconsistencies" not in st.session_state:
        st.session_state.inconsistencies = []

    def _mime_for(file):
        if not file:
            return "application/octet-stream"
        if file.type:
            return file.type
        name = (file.name or "").lower()
        if name.endswith(".csv"):
            return "text/csv"
        if name.endswith(".xlsx") or name.endswith(".xls"):
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if name.endswith(".pdf"):
            return "application/pdf"
        if name.endswith(".png"):
            return "image/png"
        if name.endswith(".jpg") or name.endswith(".jpeg"):
            return "image/jpeg"
        return "application/octet-stream"

    st.markdown("")
    process_disabled = not (assets_file and bank_file and credit_file and id_file)

    if st.button("▶️ Process Application", type="primary", disabled=process_disabled, help="Uploads the four files to /process and returns decision + final summary"):
        try:
            files_payload: List = []
            files_payload.append(("files", (assets_file.name, assets_file.getvalue(), _mime_for(assets_file))))
            files_payload.append(("files", (bank_file.name, bank_file.getvalue(), _mime_for(bank_file))))
            files_payload.append(("files", (credit_file.name, credit_file.getvalue(), _mime_for(credit_file))))
            files_payload.append(("files", (id_file.name, id_file.getvalue(), _mime_for(id_file))))

            with st.spinner("Processing…"):
                resp = requests.post(process_url, files=files_payload, timeout=180)

            if resp.status_code != 200:
                st.error(f"API error {resp.status_code}: {resp.text}")
            else:
                data = resp.json()
                st.session_state.decision_status = str(data.get("decision", ""))
                st.session_state.final_summary = str(data.get("final_summary", ""))
                st.session_state.inconsistencies = st.session_state.inconsistencies = str(data.get("inconsistencies", ""))
                st.success("Processed successfully. See the results below.")

        except Exception as e:
            st.error(f"Failed to process application: {e}")

    st.subheader("🧾 Results")
    st.text_area("Decision Status", value=st.session_state.decision_status, height=60, key="decision_status_view")
    st.text_area("inconsistencies", value=st.session_state.inconsistencies, height=220, key="inconsistencies_view")
    st.text_area("Final Summary", value=st.session_state.final_summary, height=220, key="final_summary_view")

# ---------------- Right: Chatbot ----------------
with right_col:
    st.header("💬 Knowledge Chatbot")
    st.caption("Ask questions grounded in your generated reports (RAG over the `reports/` folder).")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []  # list of dicts: {"role": "user"|"assistant", "content": str}

    # Render chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("Type your question and press Enter…")

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        try:
            payload = {"message": prompt, "directory": "reports"}
            r = requests.post(chat_url, json=payload, timeout=120)
            if r.status_code != 200:
                answer_text = f"API error {r.status_code}: {r.text}"
            else:
                answer_text = (r.json() or {}).get("answer", "").strip() or "No answer returned."
        except Exception as e:
            answer_text = f"Failed to query chatbot: {e}"

        st.session_state.chat_history.append({"role": "assistant", "content": answer_text})
        with st.chat_message("assistant"):
            st.write(answer_text)

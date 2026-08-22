import streamlit as st
import requests
import time

# ----------------------------------------------------------------------
# CONFIG — change this once your backend is deployed
# ----------------------------------------------------------------------
# FastAPI's own port — bypasses nginx entirely since streamlit and fastapi share this container
API_BASE_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="DOC/INTEL",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# STYLE — bold red / black / white, sharp edges, heavy type
# ----------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=JetBrains+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
}

.stApp {
    background-color: #0a0a0a;
    color: #f5f5f5;
}

/* Headers */
h1, h2, h3 {
    font-family: 'Archivo Black', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: -0.02em;
}

h1 {
    color: #ffffff !important;
    border-bottom: 6px solid #e8291c;
    padding-bottom: 0.3em;
    margin-bottom: 0.6em !important;
}

h2, h3 {
    color: #e8291c !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #111111;
    border-right: 3px solid #e8291c;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #e8291c !important;
}

/* Buttons */
.stButton > button {
    background-color: #e8291c;
    color: #ffffff;
    border: none;
    border-radius: 0px;
    font-family: 'Archivo Black', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.6em 1.4em;
    transition: all 0.15s ease;
    box-shadow: 4px 4px 0px #ffffff;
}

.stButton > button:hover {
    background-color: #ffffff;
    color: #e8291c;
    box-shadow: 4px 4px 0px #e8291c;
    transform: translate(-2px, -2px);
}

/* Text inputs */
.stTextInput > div > div > input,
.stTextArea textarea {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 2px solid #333333;
    border-radius: 0px;
}

.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: #e8291c;
    box-shadow: none;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 3px dashed #e8291c;
    border-radius: 0px;
    padding: 1.2em;
    background-color: #111111;
}

/* Cards / containers */
.doc-card {
    background-color: #141414;
    border-left: 6px solid #e8291c;
    padding: 1em 1.3em;
    margin-bottom: 0.8em;
    font-family: 'JetBrains Mono', monospace;
}

.status-ready {
    color: #3ddc84;
    font-weight: bold;
}
.status-processing {
    color: #e8b923;
    font-weight: bold;
}

/* Answer box */
.answer-box {
    background-color: #141414;
    border: 2px solid #e8291c;
    padding: 1.5em;
    margin-top: 1em;
    line-height: 1.6;
    font-size: 1.05em;
}

/* Q&A history item */
.qa-item {
    background-color: #141414;
    border-left: 6px solid #e8291c;
    padding: 1.2em 1.5em;
    margin-top: 1.2em;
}

.qa-question {
    color: #e8b923;
    font-weight: bold;
    font-size: 0.95em;
    margin-bottom: 0.6em;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.qa-answer {
    color: #f5f5f5;
    line-height: 1.6;
    font-size: 1.0em;
}

/* Diagonal accent bar */
.accent-bar {
    height: 10px;
    background: repeating-linear-gradient(
        135deg,
        #e8291c,
        #e8291c 12px,
        #0a0a0a 12px,
        #0a0a0a 24px
    );
    margin: 1.5em 0;
}

/* Metric-style tags */
.tag {
    display: inline-block;
    background-color: #e8291c;
    color: #ffffff;
    padding: 0.2em 0.7em;
    font-size: 0.75em;
    font-weight: bold;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

footer, #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------------
if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = None
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

# ----------------------------------------------------------------------
# SIDEBAR — AUTH
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("# DOC/\nINTEL")
    st.caption("RAG-POWERED DOCUMENT ENGINE")
    st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

    if st.session_state.token:
        st.markdown(f'<span class="tag">LOGGED IN</span>',
                    unsafe_allow_html=True)
        st.write(f"**{st.session_state.email}**")
        if st.button("LOG OUT", use_container_width=True):
            st.session_state.token = None
            st.session_state.email = None
            st.session_state.qa_history = []
            st.rerun()
    else:
        tab_login, tab_signup = st.tabs(["LOGIN", "SIGN UP"])

        with tab_login:
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input(
                "Password", type="password", key="login_password")
            if st.button("ENTER", key="login_btn", use_container_width=True):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/auth/login",
                        data={"username": login_email,
                              "password": login_password},
                    )
                    if resp.status_code == 200:
                        st.session_state.token = resp.json()["access_token"]
                        st.session_state.email = login_email
                        st.rerun()
                    else:
                        try:
                            detail = resp.json().get("detail", "LOGIN FAILED — CHECK CREDENTIALS")
                        except requests.exceptions.JSONDecodeError:
                            detail = f"LOGIN FAILED (status {resp.status_code}, empty response)"
                        st.error(detail)
                except requests.exceptions.ConnectionError:
                    st.error("CAN'T REACH API — CHECK API_BASE_URL")

        with tab_signup:
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input(
                "Password", type="password", key="signup_password")
            if st.button("CREATE ACCOUNT", key="signup_btn", use_container_width=True):
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/auth/signup",
                        json={"email": signup_email,
                              "password": signup_password},
                    )
                    if resp.status_code == 201:
                        st.success("ACCOUNT CREATED — NOW LOG IN")
                    else:
                        try:
                            detail = resp.json().get("detail", "SIGNUP FAILED")
                        except requests.exceptions.JSONDecodeError:
                            detail = f"SIGNUP FAILED (status {resp.status_code}, empty response)"
                        st.error(detail)
                except requests.exceptions.ConnectionError:
                    st.error("CAN'T REACH API — CHECK API_BASE_URL")

# ----------------------------------------------------------------------
# MAIN AREA
# ----------------------------------------------------------------------
st.markdown("# DOCUMENT INTELLIGENCE")
st.caption("UPLOAD → EMBED → RETRIEVE → GENERATE")

if not st.session_state.token:
    st.markdown('<div class="doc-card">LOG IN OR SIGN UP FROM THE SIDEBAR TO GET STARTED.</div>',
                unsafe_allow_html=True)
else:
    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    col_upload, col_status = st.columns([1, 1])

    with col_upload:
        st.markdown("## UPLOAD")
        uploaded_file = st.file_uploader(
            "Drop a PDF", type=["pdf"], label_visibility="collapsed")
        if uploaded_file and st.button("PROCESS DOCUMENT", use_container_width=True):
            with st.spinner("UPLOADING..."):
                files = {"file": (uploaded_file.name,
                                  uploaded_file.getvalue(), "application/pdf")}
                resp = requests.post(
                    f"{API_BASE_URL}/documents/upload", headers=headers, files=files)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.last_doc_id = data["document_id"]
                st.success(f"UPLOADED — STATUS: {data['status'].upper()}")
            else:
                st.error("UPLOAD FAILED")

    with col_status:
        st.markdown("## STATUS")
        if "last_doc_id" in st.session_state:
            if st.button("CHECK PROCESSING STATUS", use_container_width=True):
                resp = requests.get(
                    f"{API_BASE_URL}/documents/{st.session_state.last_doc_id}",
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    status_class = "status-ready" if data["status"] == "ready" else "status-processing"
                    st.markdown(
                        f'<div class="doc-card"><b>{data["file_name"]}</b><br>'
                        f'<span class="{status_class}">{data["status"].upper()}</span></div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("NO DOCUMENT UPLOADED YET")

    st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

    st.markdown("## ASK")
    query = st.text_input(
        "Your question", placeholder="What does this document say about...", label_visibility="collapsed")

    if st.button("GENERATE ANSWER", use_container_width=True) and query:
        answer_placeholder = st.empty()
        full_answer = ""
        try:
            with requests.get(
                f"{API_BASE_URL}/documents/ask",
                headers=headers,
                params={"query": query},
                stream=True,
            ) as resp:
                for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        full_answer += chunk
                        answer_placeholder.markdown(
                            f'<div class="answer-box">{full_answer}</div>',
                            unsafe_allow_html=True,
                        )
            # Streaming finished — save this Q&A permanently to history
            # and clear the temporary "live" box so it isn't shown twice.
            st.session_state.qa_history.append(
                {"question": query, "answer": full_answer})
            answer_placeholder.empty()
        except requests.exceptions.ConnectionError:
            st.error("CAN'T REACH API — CHECK API_BASE_URL")

    # ------------------------------------------------------------------
    # Q&A HISTORY — every past question and answer stays visible here,
    # most recent first, instead of disappearing when a new one is asked.
    # ------------------------------------------------------------------
    if st.session_state.qa_history:
        st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)
        st.markdown("## HISTORY")
        for qa in reversed(st.session_state.qa_history):
            st.markdown(
                f'<div class="qa-item">'
                f'<div class="qa-question">Q: {qa["question"]}</div>'
                f'<div class="qa-answer">{qa["answer"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)
st.caption("DOC/INTEL — BUILT WITH FASTAPI + POSTGRES + PGVECTOR + MISTRAL")

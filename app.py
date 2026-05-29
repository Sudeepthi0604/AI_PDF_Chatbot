import streamlit as st
import sqlite3
import hashlib
import secrets
import base64
import numpy as np
import faiss
from PyPDF2 import PdfReader
from google import genai
import time


# CONFIG

st.set_page_config(page_title="AI PDF Chatbot", layout="wide")

API_KEY = "AIzaSyCPfuMTrwD9Kt_lswrZq1I5RItX1cfZhdo"
client = genai.Client(api_key=API_KEY)


# DATABASE INIT

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            salt TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

init_db()


# PASSWORD HASH (PBKDF2)

def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)

    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000
    )

    return base64.b64encode(pwd_hash).decode(), salt


# CREATE USER

def create_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    pwd_hash, salt = hash_password(password)

    try:
        c.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, pwd_hash, salt)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


# VERIFY USER

def verify_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "SELECT password_hash, salt FROM users WHERE username=?",
        (username,)
    )

    result = c.fetchone()
    conn.close()

    if not result:
        return False

    stored_hash, salt = result
    new_hash, _ = hash_password(password, salt)

    return stored_hash == new_hash


# SESSION STATE

if "auth" not in st.session_state:
    st.session_state.auth = False

if "user" not in st.session_state:
    st.session_state.user = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "index" not in st.session_state:
    st.session_state.index = None

if "chunks" not in st.session_state:
    st.session_state.chunks = []

if "metadata" not in st.session_state:
    st.session_state.metadata = []


# AUTH UI

st.title("📄🔐 Production AI PDF Chatbot")

menu = st.sidebar.radio("Auth", ["Login", "Signup"])

# SIGNUP
if menu == "Signup":
    st.subheader("Create Account")

    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")

    if st.button("Signup"):
        if create_user(new_user, new_pass):
            st.success("Account created successfully")
        else:
            st.error("Username already exists")

# LOGIN
if menu == "Login":
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if verify_user(username, password):
            st.session_state.auth = True
            st.session_state.user = username
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

# BLOCK UNAUTHORIZED USERS
if not st.session_state.auth:
    st.warning("Please login to access the chatbot")
    st.stop()

# LOGOUT
st.sidebar.success(f"Logged in as: {st.session_state.user}")

if st.sidebar.button("Logout"):
    st.session_state.auth = False
    st.session_state.user = None
    st.session_state.chat_history = []
    st.session_state.index = None
    st.rerun()


# PDF FUNCTIONS

def extract_text(pdf_files):
    all_text = {}

    for pdf in pdf_files:
        reader = PdfReader(pdf)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

        all_text[pdf.name] = text

    return all_text

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []

    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])

    return chunks

# EMBEDDING FUNCTIONS

def embed_text(texts, batch_size=20):
    all_vectors = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        res = client.models.embed_content(
            model="gemini-embedding-001",
            contents=batch
        )

        vectors = np.array(
            [emb.values for emb in res.embeddings],
            dtype="float32"
        )

        all_vectors.append(vectors)

        time.sleep(0.1)

    return np.vstack(all_vectors)


# QUERY EMBEDDING (CACHED)

@st.cache_data(show_spinner=False)
def embed_query(text):
    res = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[text]
    )

    return np.array([res.embeddings[0].values], dtype="float32")


# FAISS INDEX

def build_index(all_chunks):
    vectors = embed_text(all_chunks)

    faiss.normalize_L2(vectors)

    d = vectors.shape[1]

    index = faiss.IndexFlatIP(d)
    index.add(vectors)

    return index

def search(query, index, chunks, metadata, k=5):
    q_vec = embed_query(query)

    faiss.normalize_L2(q_vec)

    _, I = index.search(q_vec, k)

    return [(metadata[i], chunks[i]) for i in I[0]]

# GEMINI ANSWER

def ask_gemini(context, question):
    prompt = f"""
You are a helpful AI assistant.

Context:
{context}

Question:
{question}

Answer clearly and simply:
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


# UI CHATBOT

st.header("📄 AI PDF Chatbot")

pdf_files = st.file_uploader(
    "Upload PDFs",
    type="pdf",
    accept_multiple_files=True
)

if st.button("Process PDFs") and pdf_files:

    all_text = extract_text(pdf_files)

    all_chunks = []
    metadata = []

    for name, text in all_text.items():
        chunks = chunk_text(text)

        for c in chunks:
            all_chunks.append(c)
            metadata.append(name)

    st.session_state.index = build_index(all_chunks)
    st.session_state.chunks = all_chunks
    st.session_state.metadata = metadata

    st.success("PDFs processed successfully!")

# SAFETY CHECK
if st.session_state.index is None:
    st.info("Upload and process PDFs first")
    st.stop()

# CHAT INPUT
question = st.text_input("Ask anything from your PDFs")

if st.button("Ask") and question:

    results = search(
        question,
        st.session_state.index,
        st.session_state.chunks,
        st.session_state.metadata
    )

    context = "\n\n".join([f"[{p}] {c}" for p, c in results])

    answer = ask_gemini(context, question)

    st.session_state.chat_history.append((question, answer))

# CHAT HISTORY
st.subheader("💬 Chat History")

for q, a in reversed(st.session_state.chat_history):
    st.markdown(f"**🧑 {st.session_state.user}:** {q}")
    st.markdown(f"**🤖 Bot:** {a}")
    st.markdown("---")
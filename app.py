import streamlit as st
import numpy as np
import faiss
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from google import genai

# -------------------------
# LOAD ENVIRONMENT VARIABLES
# -------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("Please add your GEMINI_API_KEY to the .env file")
    st.stop()

client = genai.Client(api_key=API_KEY)

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(page_title="AI Study Assistant", layout="wide", initial_sidebar_state="expanded")

# -------------------------
# CUSTOM CSS & STYLING
# -------------------------
st.markdown("""
<style>
  * {box-sizing: border-box;}

  /* Light, airy background */
  .main {
    background: linear-gradient(180deg, #f8fafc 0%, #eef6fb 50%, #f1f5f9 100%);
    color: #0b1220;
    font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
  }

  /* Hero area */
  .hero {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.5rem;
    padding: 1.25rem 1rem;
    margin-bottom: 1rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.6);
    box-shadow: 0 8px 30px rgba(15,23,42,0.06);
    overflow: visible;
  }

  .hero h1 {
    font-size: 2.25rem;
    margin: 0 0 0.25rem 0;
    background: linear-gradient(90deg,#4f46e5,#06b6d4,#60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .hero .subtitle { color: #334155; margin: 0; font-size: 0.98rem; }

  .hero-image img{ max-width: 320px; width:100%; border-radius: 12px; box-shadow: 0 10px 30px rgba(16,24,40,0.08);} 

  /* Soft cards */
  .stColumn{ background: rgba(255,255,255,0.8) !important; border: 1px solid rgba(15,23,42,0.04) !important; box-shadow: 0 8px 24px rgba(16,24,40,0.04) !important; border-radius: 12px !important; padding: 1.25rem !important;}

  .stColumn:hover{ transform: translateY(-4px); transition: all 0.28s ease; }

  /* Buttons */
  .stButton>button{ background: linear-gradient(90deg,#4f46e5,#06b6d4); color: white !important; border-radius: 10px; padding: 0.6rem 1.2rem; box-shadow: 0 8px 20px rgba(79,70,229,0.12);} 

  .stButton>button:hover{ transform: translateY(-2px); box-shadow: 0 14px 30px rgba(79,70,229,0.18); }

  /* Inputs */
  .stTextInput input, .stChatInput input, .stFileUploader input{ background: white !important; border: 1px solid rgba(15,23,42,0.06) !important; color: #0b1220 !important; border-radius: 8px !important; padding: .6rem 0.9rem !important; }

  .stTextInput input:focus, .stChatInput input:focus{ box-shadow: 0 6px 20px rgba(79,70,229,0.06) !important; border-color: rgba(79,70,229,0.25) !important; }

  /* Chat message style */
  .stChatMessage{ background: linear-gradient(180deg, #ffffff, #f8fafc) !important; border-left: 4px solid rgba(99,102,241,0.16) !important; color: #0b1220 !important; }

  /* File uploader */
  .stFileUploader>div{ border: 1px dashed rgba(15,23,42,0.06) !important; background: rgba(255,255,255,0.6) !important; }

    /* Sidebar: purple -> pink gradient, light text for contrast */
    .stSidebar{
        background: linear-gradient(180deg, #6d28d9 0%, #ec4899 100%) !important;
        color: #ffffff !important;
        border-right: none !important;
    }

    /* Ensure all sidebar text is light and high-contrast */
    .stSidebar * {
        color: #ffffff !important;
    }

    /* Radio and label contrast (soft translucent pill backgrounds) */
    .stSidebar .stRadio > label, .stSidebar .stRadio > div > label {
        color: #ffffff !important;
        font-weight: 600 !important;
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        padding: 0.45rem 0.6rem !important;
        margin-bottom: 0.4rem !important;
    }

    /* Sidebar markdown/info styling */
    .stSidebar .stMarkdown, .stSidebar .stMarkdown p {
        color: rgba(255,255,255,0.92) !important;
    }

    .stSidebar .stInfo {
        background: rgba(255,255,255,0.06) !important;
        border-left: 4px solid rgba(255,255,255,0.08) !important;
        padding: 0.6rem !important;
        border-radius: 8px !important;
        color: rgba(255,255,255,0.95) !important;
    }

  /* Floating decorative blobs */
  .blobs{ position: absolute; inset: 0; pointer-events: none; }
  .blob{ position: absolute; filter: blur(36px); opacity: 0.6; border-radius: 50%; transform: translate3d(0,0,0); }
  .b1{ width: 260px; height: 260px; background: linear-gradient(135deg,#a78bfa,#60a5fa); top:-60px; left:-60px; animation: float1 8s ease-in-out infinite; }
  .b2{ width: 180px; height: 180px; background: linear-gradient(135deg,#86efac,#34d399); bottom:-40px; right:80px; animation: float2 10s ease-in-out infinite; }
  .b3{ width: 140px; height: 140px; background: linear-gradient(135deg,#fda4af,#fb923c); top:40px; right:-40px; animation: float3 12s ease-in-out infinite; }

  @keyframes float1{ 0%{transform: translateY(0) translateX(0);}50%{transform: translateY(18px) translateX(10px);}100%{transform: translateY(0);} }
  @keyframes float2{ 0%{transform: translateY(0);}50%{transform: translateY(-14px);}100%{transform: translateY(0);} }
  @keyframes float3{ 0%{transform: translateY(0);}50%{transform: translateY(10px) translateX(-8px);}100%{transform: translateY(0);} }

  /* Animations */
  .stContainer{ animation: fadeIn 0.45s ease-out; }
  @keyframes fadeIn{ from{opacity:0; transform: translateY(8px);} to{opacity:1; transform: translateY(0);} }

</style>
""", unsafe_allow_html=True)

# -------------------------
# LOAD EMBEDDING MODEL (Cached)
# -------------------------
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

embed_model = load_embedding_model()

# -------------------------
# PERSONALITIES
# -------------------------
personalities = {
    "Friendly": """
    You are a friendly and enthusiastic Study Assistant.
    Explain simply using real-life examples.
    Ask follow-up questions.
    """,
    "Academic": """
    You are a professional university professor.
    Use structured explanations with clear headings.
    Include key definitions and concepts.
    """
}

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text


def split_text(text, chunk_size=500):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    return chunks


def create_vector_store(chunks):
    embeddings = embed_model.encode(chunks)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    return index


def retrieve_context(query, index, chunks, k=3):
    query_embedding = embed_model.encode([query])
    D, I = index.search(np.array(query_embedding), k)
    results = [chunks[i] for i in I[0]]
    return "\n".join(results)


def ask_gemini(prompt, system_instruction):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "system_instruction": system_instruction,
            "temperature": 0.4,
        }
    )
    return response.text


# -------------------------
# STREAMLIT UI
# -------------------------

# Header with styling (hero banner + decorative blobs)
st.markdown("""
<div class="hero">
    <div>
        <h1>📚 AI Study Assistant</h1>
        <p class="subtitle">Powered by RAG & Gemini AI — smart, friendly study help</p>
    </div>
    <div class="hero-image">
        <img src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&q=60&auto=format&fit=crop" alt="study illustration" />
    </div>
    <div class="blobs">
        <div class="blob b1"></div>
        <div class="blob b2"></div>
        <div class="blob b3"></div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# Sidebar for settings
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    persona = st.radio("Choose Teaching Style", list(personalities.keys()), 
                       help="Select how the AI should explain concepts")
    st.divider()
    st.markdown("### 📖 About")
    st.info("This AI Study Assistant uses RAG (Retrieval Augmented Generation) to provide accurate, context-aware answers from your PDF documents.")

# Main content area
st.markdown("### 📤 Upload Your Study Material")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", 
                                 help="Upload a PDF to start learning!")

if "vector_index" not in st.session_state:
    st.session_state.vector_index = None
    st.session_state.text_chunks = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# PDF PROCESSING
# -------------------------
if uploaded_file:
    with st.spinner("🔄 Processing your PDF... This may take a moment"):
        text = extract_text_from_pdf(uploaded_file)
        chunks = split_text(text)
        index = create_vector_store(chunks)

        st.session_state.vector_index = index
        st.session_state.text_chunks = chunks

    st.success(f"✅ PDF processed successfully! ({len(chunks)} chunks created)")

    st.markdown("### 🎯 Quick Actions")
    col1, col2, col3 = st.columns(3, gap="medium")

    # Summary
    with col1:
        st.markdown("#### 📋 Generate Summary")
        st.markdown("Create a concise overview of the document")
        if st.button("Generate Summary", key="summary_btn", use_container_width=True):
            with st.spinner("Generating summary..."):
                summary = ask_gemini(
                    f"Summarize this content:\n{text[:2000]}",
                    personalities[persona]
                )
            st.success("Summary Generated!")
            st.markdown("---")
            st.markdown(summary)

    # Notes
    with col2:
        st.markdown("#### 📝 Study Notes")
        st.markdown("Convert content into structured notes")
        if st.button("Generate Study Notes", key="notes_btn", use_container_width=True):
            with st.spinner("Creating study notes..."):
                notes = ask_gemini(
                    f"""
                    Convert this into structured study notes:
                    - Headings
                    - Bullet points
                    - Key concepts
                    - Important definitions

                    {text[:2000]}
                    """,
                    personalities[persona]
                )
            st.success("Study Notes Generated!")
            st.markdown("---")
            st.markdown(notes)

    # Quiz
    with col3:
        st.markdown("#### 🧪 Quiz Generator")
        st.markdown("Test your knowledge with MCQs")
        if st.button("Generate Quiz", key="quiz_btn", use_container_width=True):
            with st.spinner("Creating quiz questions..."):
                quiz = ask_gemini(
                    f"""
                    Generate 5 MCQs from this content.
                    Each question must have:
                    - 4 options
                    - Correct answer clearly mentioned

                    Content:
                    {text[:2000]}
                    """,
                    personalities[persona]
                )
            st.success("Quiz Generated!")
            st.markdown("---")
            st.markdown(quiz)

# -------------------------
# CHAT SECTION (RAG)
# -------------------------

st.divider()
st.markdown("### 💬 Ask Questions About Your PDF")
st.markdown("Get answers directly from your document using AI-powered search")

user_input = st.chat_input("🔍 Type your question here...", key="chat_input")

if user_input:

    if st.session_state.vector_index is not None:
        context = retrieve_context(
            user_input,
            st.session_state.vector_index,
            st.session_state.text_chunks
        )

        prompt = f"""
        Use the following context to answer the question accurately.

        Context:
        {context}

        Question:
        {user_input}
        """
    else:
        prompt = user_input

    with st.spinner("🤔 Thinking..."):
        response = ask_gemini(prompt, personalities[persona])

    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("assistant", response))

# Display Chat with better styling
st.divider()
if st.session_state.chat_history:
    st.markdown("### 📚 Conversation History")
    for role, message in reversed(st.session_state.chat_history):
        with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
            st.markdown(message)

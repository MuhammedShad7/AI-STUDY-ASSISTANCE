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
    API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    st.stop()

client = genai.Client()

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
    max-width: 1000px !important;
    margin: 0 auto !important;
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
    color: #5b21b6 !important;
  }

  .hero .subtitle { color: #334155; margin: 0; font-size: 0.98rem; }

    .hero-image img{ max-width: 320px; width:100%; border-radius: 12px; box-shadow: 0 10px 30px rgba(16,24,40,0.08); filter: brightness(0.78) saturate(0.92); opacity: 0.95; }

  /* Soft cards */
  .stColumn{ background: rgba(255,255,255,0.8) !important; border: 1px solid rgba(15,23,42,0.04) !important; box-shadow: 0 8px 24px rgba(16,24,40,0.04) !important; border-radius: 12px !important; padding: 1.25rem !important;}

  .stColumn:hover{ transform: translateY(-4px); transition: all 0.28s ease; }

  /* Buttons */
  .stButton>button{ 
    background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%) !important; 
    color: #ffffff !important; 
    border-radius: 12px !important; 
    padding: 0.75rem 1.5rem !important; 
    box-shadow: 0 8px 24px rgba(79,70,229,0.16) !important;
    border: none !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
  } 

  .stButton>button:hover { 
    transform: translateY(-3px) !important; 
    box-shadow: 0 12px 32px rgba(79,70,229,0.24) !important;
  }
  
  .stButton>button:active {
    transform: translateY(-1px) !important;
  }

  /* Inputs */
  .stTextInput input, .stChatInput input, .stFileUploader input{ background: white !important; border: 1px solid rgba(15,23,42,0.06) !important; color: #0b1220 !important; border-radius: 8px !important; padding: .6rem 0.9rem !important; }

  .stTextInput input:focus, .stChatInput input:focus{ box-shadow: 0 6px 20px rgba(79,70,229,0.06) !important; border-color: rgba(79,70,229,0.25) !important; }

  /* Chat message style */
  .stChatMessage{ background: linear-gradient(180deg, #ffffff, #f8fafc) !important; border-left: 4px solid rgba(99,102,241,0.16) !important; color: #0b1220 !important; }

    /* Ensure markdown outputs (summary, notes, quiz, chat) are highly readable */
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div {
        color: #5b21b6 !important;
        font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial !important;
        font-size: 1rem !important;
        line-height: 1.7 !important;
        font-weight: 500 !important;
    }

    /* Headings inside generated content */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, h1, h2, h3, h4, h5, h6 {
        color: #5b21b6 !important;
        font-weight: 700 !important;
    }

    /* Code blocks and preformatted text */
    .stMarkdown pre, .stMarkdown code {
        background: #f3f4f6 !important;
        color: #5b21b6 !important;
        padding: 0.6rem !important;
        border-radius: 8px !important;
        overflow: auto !important;
    }

    /* Chat messages containing markdown (assistant/user) */
    .stChatMessage .stMarkdown, .stChatMessage .stMarkdown p {
        color: #5b21b6 !important;
        font-weight: 500 !important;
    }

  /* File uploader */
  .stFileUploader>div{ border: 1px dashed rgba(15,23,42,0.06) !important; background: rgba(255,255,255,0.6) !important; }
  
  .stFileUploader label, .stFileUploader div, .stFileUploader span, .stFileUploader p {
    color: #5b21b6 !important;
    font-weight: 500 !important;
  }
  
  /* Info box styling */
  .stInfo {
    background: rgba(255,255,255,0.06) !important;
    border-left: 4px solid rgba(255,255,255,0.08) !important;
    padding: 0.6rem !important;
    border-radius: 8px !important;
    color: #5b21b6 !important;
  }
  
  .stInfo p {
    color: #5b21b6 !important;
  }
  
  /* Labels and text styling for visibility */
  label, .stLabel, .stCaption {
    color: #5b21b6 !important;
    font-weight: 500 !important;
  }
  
  /* Tab and expander text */
  .stTabs span, .stExpander span, .streamlit-expanderHeader {
    color: #5b21b6 !important;
    font-weight: 500 !important;
  }

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
        color: #ffffff !important;
    }

    .stSidebar .stInfo {
        background: rgba(255,255,255,0.06) !important;
        border-left: 4px solid rgba(255,255,255,0.08) !important;
        padding: 0.6rem !important;
        border-radius: 8px !important;
        color: #ffffff !important;
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
    try:
        reader = PdfReader(uploaded_file)
        text = ""

        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()

        if text.strip() == "":
            return None

        return text

    except Exception as e:
        st.error("❌ Failed to read PDF.")
        return None
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

    results = []
    sources = []

    for idx in I[0]:
        results.append(chunks[idx])
        sources.append(chunks[idx][:120] + "...")

    return "\n".join(results), sources


def ask_gemini(prompt, system_instruction):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.4,
            }
        )
        return response.text

    except Exception:
        return "⚠ AI service temporarily unavailable. Please try again."


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

# Initialize teaching style in session state
if "teaching_style" not in st.session_state:
    st.session_state.teaching_style = "Friendly"

# Premium Settings Section
st.markdown("""
<div style="padding: 2rem 0;">
    <h2 style="color: #5b21b6; margin-bottom: 1.5rem; font-size: 1.8rem; font-weight: 700;">⚙️ Preferences</h2>
    <div style="background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(6,182,212,0.08) 100%); 
                border: 1px solid rgba(99,102,241,0.15); border-radius: 16px; padding: 2rem; 
                box-shadow: 0 8px 32px rgba(15,23,42,0.08);">
        <div style="margin-bottom: 1.5rem;">
            <p style="color: #5b21b6; font-size: 0.95rem; font-weight: 600; margin: 0 0 1rem 0; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.8;">Teaching Style</p>
            <p style="color: #5b21b6; font-size: 0.9rem; margin: 0 0 1rem 0;">Choose how the AI explains concepts to match your learning preference</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Teaching Style Selection with visual feedback
col1, col2 = st.columns(2, gap="medium")

with col1:
    if st.button("🎓 Friendly", use_container_width=True, key="friendly_btn",
                 help="Simple explanations with examples and follow-up questions"):
        st.session_state.teaching_style = "Friendly"
        st.rerun()

with col2:
    if st.button("📚 Academic", use_container_width=True, key="academic_btn",
                 help="Structured, professional explanations with key concepts"):
        st.session_state.teaching_style = "Academic"
        st.rerun()

# Display selected style with visual confirmation
selected_style = st.session_state.teaching_style
if selected_style == "Friendly":
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(34,197,94,0.1) 0%, rgba(34,197,94,0.05) 100%); 
                border-left: 4px solid #22c55e; border-radius: 8px; padding: 0.75rem 1rem; 
                margin-top: 1rem;">
        <p style="color: #5b21b6; margin: 0; font-size: 0.9rem; font-weight: 600;">✓ Active: <strong>Friendly Mode</strong></p>
        <p style="color: #5b21b6; margin: 0.5rem 0 0 0; font-size: 0.85rem;">Simple explanations with examples</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(34,197,94,0.1) 0%, rgba(34,197,94,0.05) 100%); 
                border-left: 4px solid #22c55e; border-radius: 8px; padding: 0.75rem 1rem; 
                margin-top: 1rem;">
        <p style="color: #5b21b6; margin: 0; font-size: 0.9rem; font-weight: 600;">✓ Active: <strong>Academic Mode</strong></p>
        <p style="color: #5b21b6; margin: 0.5rem 0 0 0; font-size: 0.85rem;">Structured professional explanations</p>
    </div>
    """, unsafe_allow_html=True)

# Set persona variable for use later
persona = st.session_state.teaching_style

st.divider()

# Upload section
st.markdown("""
<div style="padding: 1.5rem 0;">
    <h2 style="color: #5b21b6; margin-bottom: 0.5rem; font-size: 1.8rem; font-weight: 700;">📤 Upload Your Study Material</h2>
    <p style="color: #5b21b6; margin: 0 0 1.5rem 0; font-size: 0.95rem;">Select a PDF document to get started with intelligent study assistance</p>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
help="Upload a PDF document to analyze and learn from. You can ask questions, generate summaries, and create quizzes based on the content of your PDF."

# About Section
st.markdown("""
<div style="padding: 2rem 0; margin-top: 1rem;">
    <h3 style="color: #5b21b6; margin-bottom: 1rem; font-size: 1.4rem; font-weight: 700;">📖 How It Works</h3>
    <div style="background: linear-gradient(135deg, rgba(6,182,212,0.08) 0%, rgba(99,102,241,0.08) 100%); 
                border: 1px solid rgba(6,182,212,0.15); border-radius: 16px; padding: 1.5rem;
                box-shadow: 0 8px 32px rgba(15,23,42,0.08);">
        <p style="color: #5b21b6; margin: 0; line-height: 1.8; font-size: 0.95rem;">
            <strong style="color: #06b6d4;">🔍 Smart Retrieval:</strong> AI extracts relevant sections from your PDF<br><br>
            <strong style="color: #06b6d4;">🧠 Intelligent Analysis:</strong> Gemini AI understands context and answers questions<br><br>
            <strong style="color: #06b6d4;">📚 Multiple Tools:</strong> Generate summaries, study notes, quizzes, and more<br><br>
            <strong style="color: #06b6d4;">⚡ Fast Processing:</strong> Get accurate answers in seconds
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

if "vector_index" not in st.session_state:
    st.session_state.vector_index = None
    st.session_state.text_chunks = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# PDF PROCESSING
# -------------------------
if uploaded_files:

    all_text = ""

    with st.spinner("🔄 Processing PDFs..."):
        for file in uploaded_files:
         text = extract_text_from_pdf(file)

        if text:
         all_text += text
        else:
         st.warning(f"⚠ Could not read {file.name}")
        if all_text.strip() == "":
         st.error("No readable text found in uploaded PDFs.")
         st.stop() 

        chunks = split_text(all_text)
        index = create_vector_store(chunks)

        st.session_state.vector_index = index
        st.session_state.text_chunks = chunks

    st.success(f"✅ {len(uploaded_files)} PDFs processed! ({len(chunks)} chunks created)")

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
if st.button("🔄 Reset Chat"):
    st.session_state.chat_history = []
    st.rerun()

user_input = st.chat_input("🔍 Type your question here...", key="chat_input")

if user_input:
    history_text = ""
    for role, msg in st.session_state.chat_history[-6:]:
        history_text += f"{role}: {msg}\n"

    # retrieve context if PDF uploaded
    if st.session_state.vector_index is not None:
        context, sources = retrieve_context(
            user_input,
            st.session_state.vector_index,
            st.session_state.text_chunks
        )

        prompt = f"""
You are having a conversation with a student.

Conversation so far:
{history_text}

Use the following context to answer accurately.

Context:
{context}

Question:
{user_input}
"""

    else:
        prompt = f"""
Conversation so far:
{history_text}

User question:
{user_input}
"""

    with st.spinner("🤔 Thinking..."):
        response = ask_gemini(prompt, personalities[persona])

    # save chat
    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("assistant", response))

    # show sources if PDF used
    if st.session_state.vector_index is not None:
        source_text = f"📖 Source Chunks: {', '.join(map(str, sources))}"
        st.session_state.chat_history.append(("assistant", source_text))

# Display Chat with better styling
st.divider()
if st.session_state.chat_history:
    st.markdown("### 📚 Conversation History")
    for role, message in reversed(st.session_state.chat_history):
        with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
            st.markdown(message)

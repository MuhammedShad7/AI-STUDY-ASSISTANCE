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
# CUSTOM CSS & STYLING - PREMIUM MODERN DESIGN
# -------------------------

import os

# Load external CSS file
def load_css():
    """Load CSS from external file"""
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as css_file:
            css_content = css_file.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ styles.css file not found. Please ensure styles.css is in the same directory as app.py")

# Apply CSS
load_css()

# -------------------------
# LOAD EMBEDDING MODEL (Cached)
# -------------------------

@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

embed_model = load_embedding_model()

# =========== SESSION STATE INITIALIZATION ===========
if "teaching_style" not in st.session_state:
    st.session_state.teaching_style = "Friendly"

if "vector_index" not in st.session_state:
    st.session_state.vector_index = None
    st.session_state.text_chunks = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =========== PERSONALITIES ===========
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


@st.cache_resource
def create_vector_store(chunks):
    embeddings = embed_model.encode(chunks, show_progress_bar=False)
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
# STREAMLIT UI - MODERN PREMIUM INTERFACE
# -------------------------

# ========== PREMIUM HERO BANNER ==========
st.markdown("""
<div class="hero-container">
    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow: hidden; border-radius: 24px; z-index: 0;">
        <div class="gradient-blob blob-1"></div>
        <div class="gradient-blob blob-2"></div>
    </div>
    <div class="hero-content" style="position: relative; z-index: 1;">
        <div class="hero-text">
            <h1>📚 AI Study Assistant</h1>
            <p class="hero-subtitle">Powered by advanced RAG & Gemini AI • Smart, adaptive learning companion</p>
            <div style="display: flex; gap: 1rem; margin-top: 1.5rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">⚡</span>
                    <span style="color: #94a3b8; font-size: 0.9rem;"><strong>Instant</strong> answers</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">🎯</span>
                    <span style="color: #94a3b8; font-size: 0.9rem;"><strong>Accurate</strong> retrieval</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.5rem;">📈</span>
                    <span style="color: #94a3b8; font-size: 0.9rem;"><strong>Learning</strong> tools</span>
                </div>
            </div>
        </div>
        <div class="hero-image">
            <img src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=500&q=80&auto=format&fit=crop" alt="Study Illustration" />
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# ========== PREFERENCES SECTION ==========
st.markdown("""
<div style="margin: 2.5rem 0 1.5rem 0;">
    <h2>⚙️ Preferences & Settings</h2>
    <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 0.95rem;">Customize your learning experience</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="glass-card">
    <div style="margin-bottom: 1.5rem;">
        <p style="color: #06b6d4; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin: 0; opacity: 0.9;">📖 Teaching Style</p>
        <p style="color: #cbd5e1; font-size: 0.95rem; margin: 0.75rem 0 0 0; line-height: 1.5;">Choose how the AI explains concepts to match your learning preference</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Teaching Style Selection with modern UI
col1, col2 = st.columns(2, gap="large")

with col1:
    if st.button("🎓 Friendly Tutor", use_container_width=True, key="friendly_btn",
                 help="Simple explanations with real-world examples and follow-up questions"):
        st.session_state.teaching_style = "Friendly"
        st.rerun()

with col2:
    if st.button("📚 Academic Mode", use_container_width=True, key="academic_btn",
                 help="Structured professional explanations with key concepts and definitions"):
        st.session_state.teaching_style = "Academic"
        st.rerun()

# Visual confirmation of selected style with animation
selected_style = st.session_state.teaching_style
st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

if selected_style == "Friendly":
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(34,197,94,0.15) 0%, rgba(34,197,94,0.08) 100%); 
                border: 1px solid rgba(34,197,94,0.4); 
                border-left: 4px solid #22c55e;
                border-radius: 12px; padding: 1rem 1.25rem; 
                box-shadow: 0 10px 30px rgba(34,197,94,0.1);
                animation: slideInLeft 0.3s ease-out;">
        <p style="color: #22c55e; margin: 0; font-size: 0.95rem; font-weight: 600;">✓ Active: Friendly Tutor Mode</p>
        <p style="color: #86efac; margin: 0.5rem 0 0 0; font-size: 0.85rem;">Explanations optimized for understanding with examples</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(34,197,94,0.15) 0%, rgba(34,197,94,0.08) 100%); 
                border: 1px solid rgba(34,197,94,0.4); 
                border-left: 4px solid #22c55e;
                border-radius: 12px; padding: 1rem 1.25rem; 
                box-shadow: 0 10px 30px rgba(34,197,94,0.1);
                animation: slideInLeft 0.3s ease-out;">
        <p style="color: #22c55e; margin: 0; font-size: 0.95rem; font-weight: 600;">✓ Active: Academic Mode</p>
        <p style="color: #86efac; margin: 0.5rem 0 0 0; font-size: 0.85rem;">Professional, structured explanations with academic rigor</p>
    </div>
    """, unsafe_allow_html=True)

# Set persona variable for use later
persona = st.session_state.teaching_style

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
st.divider()

# ========== MODERN UPLOAD SECTION ==========
st.markdown("""
<div style="margin: 2.5rem 0 1.5rem 0;">
    <h2>📤 Upload Your Study Material</h2>
    <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 0.95rem;">Upload PDF documents to unlock intelligent analysis and Q&A</p>
    <div style="display: flex; gap: 2rem; margin-top: 1.5rem; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.25rem; color: #06b6d4;">🔍</span>
            <div>
                <p style="color: #06b6d4; font-size: 0.9rem; font-weight: 600; margin: 0;">Smart Retrieval</p>
                <p style="color: #64748b; font-size: 0.85rem; margin: 0.25rem 0 0 0;">Extract relevant insights</p>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.25rem; color: #06b6d4;">⚡</span>
            <div>
                <p style="color: #06b6d4; font-size: 0.9rem; font-weight: 600; margin: 0;">Lightning Fast</p>
                <p style="color: #64748b; font-size: 0.85rem; margin: 0.25rem 0 0 0;">Process in seconds</p>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.25rem; color: #06b6d4;">🧠</span>
            <div>
                <p style="color: #06b6d4; font-size: 0.9rem; font-weight: 600; margin: 0;">Context Aware</p>
                <p style="color: #64748b; font-size: 0.85rem; margin: 0.25rem 0 0 0;">Understand relationships</p>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Drop PDFs here or click to browse",
    type="pdf",
    accept_multiple_files=True,
    help="Upload one or multiple PDF files to analyze and ask questions about them.\nSupports text extraction with intelligent chunking for optimal retrieval.",
    label_visibility="collapsed"
)

# PDF PROCESSING & QUICK ACTIONS
# ========================================
import time

if uploaded_files:
    start_time = time.time()
    all_text = ""

    with st.spinner("🔄 Processing your PDFs..."):
        for file in uploaded_files:
            text = extract_text_from_pdf(file)
            if text:
                all_text += text
            else:
                st.warning(f"⚠️ Could not extract text from {file.name}")

        if all_text.strip() == "":
            st.error("❌ No readable text found in uploaded PDFs. Please try another file.")
            st.stop()

        chunks = split_text(all_text)
        index = create_vector_store(chunks)
        st.session_state.vector_index = index
        st.session_state.text_chunks = chunks

    elapsed = time.time() - start_time

    # Success Banner with Modern Styling
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(34,197,94,0.15) 0%, rgba(34,197,94,0.08) 100%); 
                border: 1px solid rgba(34,197,94,0.4); 
                border-left: 4px solid #22c55e;
                border-radius: 12px; padding: 1.25rem; 
                box-shadow: 0 10px 30px rgba(34,197,94,0.1);
                margin: 1.5rem 0;">
        <p style="color: #22c55e; margin: 0; font-size: 0.95rem; font-weight: 600;">✓ PDFs Processed Successfully</p>
        <p style="color: #86efac; margin: 0.5rem 0 0 0; font-size: 0.85rem;">""" + 
        f"{len(uploaded_files)} file(s) processed • {len(chunks)} chunks created • {elapsed:.2f}s processing time" +
        """</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ========== QUICK ACTIONS - MODERN CARDS ==========
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <h3>🎯 Quick Actions</h3>
        <p style="color: #94a3b8; margin-top: 0.25rem; font-size: 0.9rem;">Generate study materials with AI assistance</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="large")

    # Summary Card
    with col1:
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📋</div>
            <h4 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">Generate Summary</h4>
            <p style="color: #94a3b8; font-size: 0.85rem; margin: 0 0 1rem 0;">Create a concise overview of the document</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Generate", key="summary_btn", use_container_width=True):
            with st.spinner("✨ Generating summary..."):
                summary = ask_gemini(
                    f"Summarize this content in a structured format:\n{text[:2000]}",
                    personalities[persona]
                )
            st.success("✓ Summary Generated!")
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            st.markdown(summary)

    # Study Notes Card
    with col2:
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📝</div>
            <h4 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">Study Notes</h4>
            <p style="color: #94a3b8; font-size: 0.85rem; margin: 0 0 1rem 0;">Convert content into structured notes</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Generate", key="notes_btn", use_container_width=True):
            with st.spinner("✨ Creating study notes..."):
                notes = ask_gemini(
                    f"""
                    Convert this into well-structured study notes with:
                    • Clear section headings
                    • Bullet points for key ideas
                    • Important definitions highlighted
                    • Practical examples

                    Content:
                    {text[:2000]}
                    """,
                    personalities[persona]
                )
            st.success("✓ Study Notes Generated!")
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            st.markdown(notes)

    # Quiz Card
    with col3:
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🧪</div>
            <h4 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">Quiz Generator</h4>
            <p style="color: #94a3b8; font-size: 0.85rem; margin: 0 0 1rem 0;">Test your knowledge with MCQs</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Generate", key="quiz_btn", use_container_width=True):
            with st.spinner("✨ Creating quiz questions..."):
                quiz = ask_gemini(
                    f"""
                    Generate 5 challenging multiple-choice questions from this content.
                    Format each question with:
                    • The question
                    • 4 distinct options (A, B, C, D)
                    • Correct answer with explanation

                    Content:
                    {text[:2000]}
                    """,
                    personalities[persona]
                )
            st.success("✓ Quiz Generated!")
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            st.markdown(quiz)

# ========== MODERN CHAT INTERFACE ==========
st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
st.divider()
st.markdown("""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2>💬 Ask Questions About Your PDFs</h2>
    <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 0.95rem;">Get intelligent, context-aware answers powered by advanced RAG</p>
</div>
""", unsafe_allow_html=True)

# Reset Chat Button
col_left, col_right = st.columns([1, 4])
with col_left:
    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# Chat Input
user_input = st.chat_input(
    "💭 Ask anything about your PDFs...",
    key="chat_input"
)

if user_input:
    history_text = ""
    for role, msg in st.session_state.chat_history[-6:]:
        history_text += f"{role}: {msg}\n"

    # Retrieve context if PDF uploaded
    if st.session_state.vector_index is not None:
        context, sources = retrieve_context(
            user_input,
            st.session_state.vector_index,
            st.session_state.text_chunks
        )

        prompt = f"""
You are an intelligent study assistant having a conversation with a student. Be helpful, clear, and accurate.

Previous conversation:
{history_text}

Use this context from the document to answer accurately:
{context}

Student's question:
{user_input}
"""

    else:
        prompt = f"""
Previous conversation:
{history_text}

Student's question:
{user_input}
"""

    with st.spinner("🤔 Thinking..."):
        response = ask_gemini(prompt, personalities[persona])

    # Save to chat history
    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("assistant", response))

    # Add source metadata if available
    if st.session_state.vector_index is not None:
        source_info = f"📖 Retrieved from {len(sources)} document segment(s)"
        st.session_state.chat_history.append(("system", source_info))

# ========== CHAT DISPLAY WITH MODERN STYLING ==========
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
if st.session_state.chat_history:
    st.markdown("""
    <div style="margin: 2rem 0 1rem 0;">
        <h3>📚 Conversation History</h3>
        <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.25rem;">Your learning companion's responses</p>
    </div>
    """, unsafe_allow_html=True)

    for idx, (role, message) in enumerate(st.session_state.chat_history):
        if role == "system":
            st.markdown(f"""
            <div style="background: rgba(6,182,212,0.08); border-left: 4px solid #06b6d4; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.75rem; font-size: 0.85rem; color: #94a3b8;">
                {message}
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
                st.markdown(message)

import os
import io
from typing import List, Tuple

import streamlit as st
from PyPDF2 import PdfReader
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
import openai
import dotenv
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

@st.cache_resource
def load_embedder(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    return SentenceTransformer(model_name)


def extract_text_from_pdf(uploaded_file) -> str:
    # uploaded_file is a Streamlit UploadedFile; read bytes
    reader = PdfReader(io.BytesIO(uploaded_file.read()))
    texts = []
    for p in reader.pages:
        try:
            texts.append(p.extract_text() or "")
        except Exception:
            # best-effort
            texts.append("")
    return "\n\n".join(texts)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i : i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks


@st.cache_resource
def build_vectorstore(chunks: List[str], _embedder: SentenceTransformer) -> Tuple[NearestNeighbors, np.ndarray]:
    # Use the underscore version _embedder inside the function
    embeddings = _embedder.encode(chunks, show_progress_bar=False)
    nn = NearestNeighbors(n_neighbors=5, metric="cosine")
    nn.fit(embeddings)
    return nn, np.array(embeddings)


def query_vectorstore(query: str, embedder: SentenceTransformer, nn: NearestNeighbors, embeddings: np.ndarray, chunks: List[str], top_k: int = 4):
    q_emb = embedder.encode([query])[0]
    dists, idxs = nn.kneighbors([q_emb], n_neighbors=min(top_k, len(chunks)))
    # sklearn returns distances for cosine metric in [0,2] where smaller is closer
    idxs = idxs[0]
    results = [(chunks[i], float(dists[0][k])) for k, i in enumerate(idxs)]
    return results
def call_llm(system_prompt: str, user_prompt: str, model_name: str = "gemini-3-flash-preview") -> str:
    api_key = os.environ.get("GEMINI_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_KEY not set")

    genai.configure(api_key=api_key)
    
    model_obj = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt
    )

    try:
        response = model_obj.generate_content(
            user_prompt,
            generation_config={
                "thinking_config": {"include_thoughts": True}
            }
        )
    except Exception:
        response = model_obj.generate_content(user_prompt)
        
    return response.text


def main():
    st.set_page_config(page_title="PDF Q&A", layout="wide")
    st.title("PDF Q&A — upload a PDF and ask questions")

    st.sidebar.header("Settings")
    st.sidebar.markdown("Set API key in `GEMINI_KEY`.")
    model = st.sidebar.selectbox(
        "LLM model", 
        ["gemini-3-flash-preview", "gemini-3.1-flash-lite-preview"], 
        index=0
    )

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if uploaded_file is not None:
        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(uploaded_file)

        if not text.strip():
            st.error("No extractable text found in PDF.")
            return

        st.success("Text extracted — building embeddings...")
        
        # 1. Create the chunks
        chunks = chunk_text(text, chunk_size=500, overlap=100)
        st.write(f"Document split into {len(chunks)} chunks.")

        # 2. Build the vector store
        embedder = load_embedder()
        nn, embeddings = build_vectorstore(chunks, embedder)

        st.header("Ask a question about the PDF")
        question = st.text_input("Your question")
        
        if st.button("Get answer") and question.strip():
            with st.spinner("Searching for relevant passages..."):
                # 3. Get results ONLY after the button is clicked
                results = query_vectorstore(question, embedder, nn, embeddings, chunks, top_k=4)

            # 4. Build context using the renamed variable 'chunk' to avoid collision
            context_texts = []
            for i, (chunk, dist) in enumerate(results):
                context_texts.append(f"Passage {i+1} (score={dist:.3f}):\n{chunk}")

            system_prompt = "You are an assistant... (concise version)"
            user_prompt = "Context:\n\n" + "\n\n".join(context_texts) + f"\n\nQuestion: {question}"

            with st.spinner("Querying LLM..."):
                try:
                    answer = call_llm(system_prompt, user_prompt, model_name=model)
                    st.subheader("Answer")
                    st.write(answer)
                except Exception as e:
                    st.error(f"LLM call failed: {e}")
                    return

            st.subheader("Cited passages")
            for i, (chunk, dist) in enumerate(results):
                st.markdown(f"**Passage {i+1} (score={dist:.3f})**")
                st.write(chunk[:1000] + ("..." if len(chunk) > 1000 else ""))
    else:
        st.info("Upload a PDF to get started.")


if __name__ == "__main__":
    main()

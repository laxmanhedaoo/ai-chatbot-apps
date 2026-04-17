# PDF Q&A Streamlit app

This small Streamlit app lets a user upload a PDF and ask questions about its contents. It:

- extracts text from the uploaded PDF
- chunks the text and computes local embeddings using sentence-transformers
- performs a nearest-neighbour search to find relevant passages
- sends the passage(s) + the user question to an LLM to generate an answer

This is a **Retrieval-Augmented Generation (RAG)**. It allows users to upload PDF documents and ask questions based on the content. The app performs local vector search to find relevant passages and uses Google Gemini to generate context-aware answers.

## 🚀 Features

- **Local Semantic Search**: Uses `sentence-transformers` (`all-MiniLM-L6-v2`) to create embeddings locally.
- **Efficient Retrieval**: Uses Scikit-learn's `NearestNeighbors` for fast cosine similarity search.
- **Advanced LLM Support**: Integrated with Google Gemini 3 models (Flash/Lite) for high-speed reasoning.
- **Thinking Config**: Leverages Gemini’s "thinking" capabilities for more detailed and accurate responses.
- **Citations & Scores**: Displays the exact passages retrieved from the PDF along with their similarity scores.


## 🛠️ Technical Architecture

1.  **Extraction**: Raw text is extracted from PDFs using `PyPDF2`.
2.  **Chunking**: Text is split into 500-word chunks with a 100-word overlap to preserve context.
3.  **Vectorization**: Chunks are converted into vectors using a local transformer model.
4.  **Retrieval**: A query is embedded, and the top 4 most similar chunks are retrieved using Nearest Neighbors.
5.  **Generation**: The context is passed to Gemini with a specialized system prompt to generate a grounded answer.



## 📋 Prerequisites

- **Python**: 3.9+
- **Google AI API Key**: Obtain one from here [Google AI Studio](https://aistudio.google.com/).




Notes about API keys
- The app expects a key in the environment variable `GEMINI_KEY`. For convenience the app will copy `GEMINI_KEY` into `OPENAI_API_KEY` so OpenAI-compatible Python clients (the `openai` package) can be used. If you'd rather use a different key name, set `OPENAI_API_KEY` directly.

Quick start (macOS, zsh):

## ⚙️ Setup & Installation

1. create and activate a virtualenv (optional but recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
### OR
# Install required packages
```bash
pip install streamlit PyPDF2 numpy sentence-transformers scikit-learn openai python-dotenv google-generativeai
```

2. set your key and run Streamlit:

a. .env file 

b. Key is GEMINI_KEY=Your api key
```bash
streamlit run app.py
```

3. In the browser, upload a PDF and ask questions.

Security note: keep your API keys secret. This app copies `GEMINI_KEY` to only locally in the process.

If you want the app to use a different LLM or a direct Gemini/Vertex AI client, modify the `call_llm` function in `app.py`.


A versatile dashboard built with Streamlit that integrates data visualization, a functional calculator, and an AI-powered chatbot using Google's Gemini Pro model.

## ✨ Features

-   **🏠 Home:** Personalized greeting interface.
-   **📊 Data Visualization:** Interactive data tables and line charts generated using NumPy and Pandas.
-   **🧮 Calculator:** A simple tool for basic arithmetic operations (Add, Subtract, Multiply).
-   **💬 Gemini Chatbot:** A sophisticated chat interface with custom CSS styling, avatars, and persistent session state, powered by the `gemini-3-flash-preview` model.

## 🛠️ Tech Stack

-   **Frontend:** [Streamlit](https://streamlit.io/)
-   **AI Model:** [Google Generative AI (Gemini)](https://ai.google.dev/)
-   **Data Processing:** [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
-   **Environment Management:** `python-dotenv`

## 📋 Prerequisites

Before running the application, ensure you have the following:

1.  Python 3.9+
2.  A Google AI Studio API Key. Get one [here](https://aistudio.google.com/).

## 🚀 Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/laxmanhedaoo/ai-chatbot-apps
        cd ai-chatbot-apps
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\\Scripts\\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install streamlit pandas numpy google-generativeai python-dotenv
    ```
    or
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add your Gemini API key:
    ```env
    GEMINI_API_KEY=your_actual_api_key_here
    ```

## 🏃 Running the App

Start the Streamlit server by running:

```bash
streamlit run app.py
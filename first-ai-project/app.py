import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')
# Title
st.title("Multi-Feature Streamlit App 🚀")

# Sidebar
st.sidebar.title("Navigation")
option = st.sidebar.radio(
    "Choose a feature:",
    ["Home", "Data Visualization", "Calculator", "Chatbot"]
)

# --- Home ---
if option == "Home":
    st.header("🏠 Home")
    name = st.text_input("Enter your name:")
    
    if name:
        st.success(f"Welcome {name} 👋")

# --- Data Visualization ---
elif option == "Data Visualization":
    st.header("📊 Data Visualization")

    data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['A', 'B', 'C']
    )

    st.dataframe(data)
    st.line_chart(data)

# --- Calculator ---
elif option == "Calculator":
    st.header("🧮 Calculator")

    num1 = st.number_input("Enter first number")
    num2 = st.number_input("Enter second number")

    operation = st.selectbox("Operation", ["Add", "Subtract", "Multiply"])

    if st.button("Calculate"):
        if operation == "Add":
            result = num1 + num2
        elif operation == "Subtract":
            result = num1 - num2
        else:
            result = num1 * num2

        st.success(f"Result: {result}")


elif option == "Chatbot":
    st.header("💬 Gemini Chatbot")

    # 1. Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "agent", "content": "I'm your conversational agent, what can we talk about today?"}
        ]

    # 2. Input Box (Pinned after header)
    prompt = st.chat_input("Ask something...")

    # 3. Custom CSS for Layout & Avatars
    st.markdown("""
        <style>
        /* Force input to stay under header */
        [data-testid="stChatInput"] {
            position: static !important;
            padding: 10px 0px !important;
        }

        .message-row {
            display: flex;
            margin-bottom: 20px;
            width: 100%;
            align-items: center;
        }

        .user-row { justify-content: flex-end; }
        .agent-row { justify-content: flex-start; }

        .bubble {
            padding: 12px 18px;
            border-radius: 20px;
            max-width: 80%;
            font-size: 14px;
            color: white;
            line-height: 1.5;
        }

        .user-bubble { background-color: #2b2b2b; margin-right: 12px; }
        .agent-bubble { 
            background-color: #1e1e1e; 
            border: 1px solid #333; 
            margin-left: 12px; 
        }

        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
        }
        </style>
    """, unsafe_allow_html=True)

    # 4. Handle Logic
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        try:
            response = model.generate_content(prompt)
            st.session_state.messages.append({"role": "agent", "content": response.text})
        except Exception as e:
            st.session_state.messages.append({"role": "agent", "content": f"Error: {e}"})

    # 5. Scrollable Chat Container
    # height=500 sets the window size; border=False keeps it clean
    with st.container(height=500, border=False):
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                    <div class="message-row user-row">
                        <div class="bubble user-bubble">{msg['content']}</div>
                        <img src="https://api.dicebear.com/7.x/adventurer/svg?seed=Felix" class="avatar">
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="message-row agent-row">
                        <img src="https://api.dicebear.com/7.x/bottts/svg?seed=Aneka" class="avatar">
                        <div class="bubble agent-bubble">{msg['content']}</div>
                    </div>
                """, unsafe_allow_html=True)
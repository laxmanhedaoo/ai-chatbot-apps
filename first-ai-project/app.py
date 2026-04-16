import streamlit as st
import pandas as pd
import numpy as np

# Title
st.title("Multi-Feature Streamlit App 🚀")

# Sidebar
st.sidebar.title("Navigation")
option = st.sidebar.radio(
    "Choose a feature:",
    ["Home", "Data Visualization", "Calculator"]
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
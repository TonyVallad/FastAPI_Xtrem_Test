import streamlit as st

st.set_page_config(
    page_title="FastAPI Xtrem",
    page_icon="🚀",
    layout="wide"
)

def main():
    st.title("🚀 FastAPI Xtrem")
    st.subheader("Welcome to the FastAPI Xtrem Application")
    st.write("Please use the sidebar navigation to explore different sections of the application.")
    
    st.info("This is the main page of the FastAPI Xtrem application. Please login to access more features.")

if __name__ == "__main__":
    main() 
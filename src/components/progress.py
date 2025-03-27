import streamlit as st

def show_progress(task_id: str, description: str):
    progress = st.progress(0)
    status = st.status(description)
    return progress, status

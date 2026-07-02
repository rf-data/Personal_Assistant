## A_p3_emails.py
# imports
import streamlit as st


def show():
    st.header("🏠 Startseite ")
    st.subheader("**LLM processing**")

    st.divider()

    summary, merge = st.tabs(["Summarize file(s)",
                              "Merge file content"])

    with summary:
        st.markdown("**Under Construction**")

    with merge:
        st.markdown("**Under Construction**")

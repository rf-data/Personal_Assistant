"""Run with: python -m streamlit run lecture_summarizer_app.py --server.address 127.0.0.1"""

import streamlit as st

from frontend.pages.G_p0_lecture_summarizer import show

st.set_page_config(page_title="Lecture Summarizer", layout="wide")
show()

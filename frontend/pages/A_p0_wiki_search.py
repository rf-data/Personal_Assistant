## A_p0_wiki_search.py
# imports
import streamlit as st

from src.core.memory import app_session, ParseContext
from src.tools_parsing.search_wiki import wiki_article_search


def show():
    st.header("🏠 Startseite ")
    st.subheader("**Wikipedia Query**")

    st.divider()

    # st.markdown("Enter your ")

    st.markdown("**Enter a query**")
    query = st.text_input(
                        label="Enter the query",
                        placeholder=""
                        )
    
    results = None
    # general_cfg = session_state.general_settings
    if st.button("Start query"):
        # st.write("Why hello there")

        # from src.core.memory import app_session

        parse_context = ParseContext()
        parse_context.parse_settings = app_session.parse_settings
        parse_context.parse_settings.wiki.query = query
        parse_context.logger = app_session.logger

        # query_cmd = ["python", "-u", "-m", "src.tools.search_wiki"]

        # live_command_demo(query_cmd)
        results = wiki_article_search(
                            run_context=parse_context
                            )

    if results:
        with st.popover("**Results**"):      
            st.json(results.model_dump())


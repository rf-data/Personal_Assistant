## B_p2_ETL_wiki_page
# imports
from datetime import datetime

import streamlit as st

from src.core.memory import ParseContext, app_session
from src.tools_parsing.search_wiki import wiki_article_search


def show():
    # st.header("🏠 Startseite ")

    st.subheader("**Wikipedia Query**")

    st.divider()

    # st.markdown("Enter your ")

    st.markdown("**Enter a query**")
    query = st.text_input(label="Enter the query", placeholder="")

    results = None
    # general_cfg = session_state.general_settings
    if st.button("Start query"):
        # st.write("Why hello there")

        # from src.core.memory import app_session

        parse_config = app_session.parse_settings
        parse_config.wiki.query = query

        parse_context = ParseContext(
                        parse_settings=app_session.parse_settings
                        )

        parse_context.logger = app_session.logger

        # query_cmd = ["python", "-u", "-m", "src.tools.search_wiki"]

        # live_command_demo(query_cmd)
        results = wiki_article_search(parse_context=parse_context)

    if results:
        with st.popover("**Results**"):
            st.json(results.model_dump())

    st.divider()

    st.subheader("**'Extracting content from Wikipedia'**")

    st.divider()

    st.markdown("**SOURCE**")
    st.write("Enter the (a) Page_ID or (b) query + query_time.")

    col1, col2 = st.columns(2, border=True)

    with col1:
        # st.markdown("")
        page_id = st.number_input(label="**Enter Page_ID(s)**")

    with col2:
        st.markdown("**Enter a query and the corresponding query_time**")
        query = st.text_input(label="Enter the query", placeholder="")

        st.text_input(
            "Placeholder for the other text input widget",
            "This is a placeholder",
            key="placeholder",
        )

        query_time = st.datetime_input(
            "When was the query time?",
            format="YYYY-MM-DD_hh-mm-ss",
            value=None,
            max_value=datetime.now(),
        )

    event_time = st.datetime_input("Schedule your event", value=None)
    st.write("Event scheduled for", event_time)

    if page_id and query and query_time:
        st.error("Provide either Page_ID(s) or query + query_time")

    st.divider()

    st.markdown("**SETTINGS")

    run_config = {}

    run_config["assemble_as_md"] = st.radio(
        "🎯 Should the extracted html-text assembled as md-file?",
        options=[True, False],
        index=None,
    )
    run_config["scrape_images"] = st.radio(
        "🎯 Should available images in html text be scraped?",
        options=[True, False],
        index=None,
    )
    options = st.multiselect(
        "🎯 At which stages files should be saved?", options=["info", "html", "md"]
    )
    st.write("You selected:", options)
    run_config["save"] = [options]
    # import streamlit as st

    # options = st.multiselect(
    #     "What are your favorite colors?",
    #     ["Green", "Yellow", "Red", "Blue"],
    #     default=["Yellow", "Red"],
    # )

    #
    if query and query_time and not page_id:
        # TODO: connect 'options' to page_ids in query_JSON

        run_config["article_to_parse"] = st.selectbox(
            "🎯 Which pages should be scraped?",
            options=["raw_dict", "words"],
            index=None,
            placeholder="Wähle eine Datei...",
        )
    run_config["language"] = st.selectbox(
        "🎯 Which wikipedia should be used?", options=["english", "german"], index=None
    )

    # session_state.run_config = run_config

    st.divider()

    st.markdown("**PARSING**")

## B_p2_ETL_wiki_page
# imports 
import streamlit as st
from datetime import datetime


def show():
    # st.header("🏠 Startseite ")
    st.subheader("**'Extracting content from Wikipedia'**")

    st.divider()

    st.markdown("**SOURCE**")
    st.write("Enter the (a) Page_ID or (b) query + query_time.")

    col1, col2 = st.columns(2, border=True)

    with col1:
        st.markdown("**Enter Page_ID(s)**")
        page_id = st.number_input()

    with col2:
        st.markdown("**Enter a query and the corresponding query_time**")
        query = st.text_input(
                        label="Enter the query",
                        placeholder=""
                        )

        st.text_input(
        "Placeholder for the other text input widget",
        "This is a placeholder",
        key="placeholder",
    )

        query_time = st.datetime_input(
                                    "When was the query time?",
                                    format="YYYY-MM-DD_hh-mm-ss",
                                    value=None,
                                    max_value=datetime.now()
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
                    index=None
                )
    run_config["scrape_images"] = st.radio(
                    "🎯 Should available images in html text be scraped?",
                    options=[True, False],
                    index=None
                )
    options = st.multiselect(
                    "🎯 At which stages files should be saved?",
                    options=["info", "html", "md"]
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
                        placeholder="Wähle eine Datei..."
                )
    run_config["language"] = st.selectbox(
                    "🎯 Which wikipedia should be used?",
                    options=["english", "german"],
                    index=None
                )
    
    # session_state.run_config = run_config

    st.divider()

    st.markdown("**PARSING**")

    

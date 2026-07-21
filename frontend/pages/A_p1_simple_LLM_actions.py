## A_p3_emails.py
# imports
from typing import Literal

import streamlit as st
from pydantic import BaseModel


class MarvinContext(BaseModel):
    data: str
    target: Literal[""]
    n_targets: int
    instructions: str
    labels: list
    multi_label_: bool


def show():
    st.header("🏠 Startseite ")
    st.subheader("**'Simple' LLM processing**")

    st.divider()

    llm_file = st.selectbox(  # selectbox, multiselect(
        label="Which pdf file(s) should be parsed?",
        options=list(Path(input_data).rglob("*.pdf")),
        format_func=lambda p: shorten_path(p, n=1),
        key="pdf_files",
    )

    m_context = MarvinContext(data=read_text_file(llm_file))

    action = st.pills(
        label="Choose a LLM process",
        options=[
            "cast",
            "classify",
            "extract",
            "generate",
            "summarize",
            # "say",
        ],
    )

    match action:
        case "cast":
            target = st.pills(
                label="target data type", options=["str", "int", "float", "bool"]
            )
            m_context.target = target

            instruct = st.text_area(label="instruction", value=None, max_chars=250)
            m_context.instructions = instruct

            st.write(
                f"You wrote {len(instruct) if instruct is not None else '0'} characters."
            )

        case "classify":
            multi_label = st.toggle(label="enable multi-labelling")
            m_context.multi_label = multi_label

            labels = st.multiselect(
                label="Which labels should be used?",
                options=[],
                max_selections=5,
                accept_new_options=True,
            )
            m_context.label = labels
            st.write("You selected:", labels)

            instruct = st.text_area(label="instruction", value=None, max_chars=250)
            m_context.instructions = instruct
            st.write(
                f"You wrote {len(instruct) if instruct is not None else '0'} characters."
            )

        case "extract":
            target = st.pills(
                label="target data type", options=["str", "int", "float", "bool"]
            )
            m_context.target = target

            instruct = st.text_area(label="instruction", value=None, max_chars=250)
            m_context.instructions = instruct
            st.write(
                f"You wrote {len(instruct) if instruct is not None else '0'} characters."
            )

        case "generate":
            target = st.pills(
                label="target data type", options=["str", "int", "float", "bool"]
            )
            m_context.target = target
            n_target = st.slider(
                label="How many target should be generated?",
                min_value=1,
                max_value=None,
                step=1,
            )
            m_context.n_target = n_target
            st.write(f"You selected: --> 'generate {n_target} *{target}* objects'")
            # ", n_target)

            instruct = st.text_area(label="instruction", value=None, max_chars=250)
            m_context.instructions = instruct
            st.write(
                f"You wrote {len(instruct) if instruct is not None else '0'} characters."
            )

        case "summarize":
            instruct = st.text_area(label="instruction", value=None, max_chars=250)
            m_context.instructions = instruct
            st.write(
                f"You wrote {len(instruct) if instruct is not None else '0'} characters."
            )

    # summary, merge = st.tabs(["Summarize file(s)",
    #                           "Merge file content"])

    # with summary:
    #     st.markdown("**Under Construction**")

    # with merge:
    #     st.markdown("**Under Construction**")

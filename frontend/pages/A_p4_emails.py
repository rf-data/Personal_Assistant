## A_p4_emails.py
# imports
import imaplib
import email
import streamlit as st

from src.core.config import organizer_env_vars as organizer

# from src.core.logger import create_logger
# from src.core.memory import app_session
from src.utils.email_helper import (
    context_imap_connection,
    get_mailbox_status,
    # fetch_unseen_mails,
    list_mailboxes,
)


def show():
    st.header("🏠 Startseite ")
    st.subheader("**E-Mails**")

    st.divider()

    # st.markdown("**Under Construction**")

    # step 1

    with st.expander("**Mail boxes**"):
        with context_imap_connection(organizer) as mail:
            # list mail box folders
            boxes = list_mailboxes(mail)

            for box in boxes:
                box = get_mailbox_status(mail, box)

                box_info = {
                    "**Name mailbox**": box.name,
                    "**Total emails**": box.total_messages,
                    "**Unseen emails**": box.unread_messages,
                }

                st.json(box_info)
                st.write()

    with st.expander("PLACEHOLDER **New mails**"):
        st.info("PLACEHOLDER **fetch_mails()**")

    with st.expander("PLACEHOLDER **Filtered mails**"):
        st.info("PLACEHOLDER **fetch_mails()**")

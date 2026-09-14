# ## email.py
# # import
from email import policy
from email.parser import BytesParser

from src.core.config import organizer_env_vars as organizer
from src.core.logger import create_logger
from src.core.memory import app_session
from src.utils.email_helper import (
    context_imap_connection,
    fetch_unseen_mails,
    get_sent_datetime,
    parse_internal_date,
)


def check_mailbox(
    organizer: OrganizerSettings,
    mailbox_name: str = "INBOX",
    criteria: tuple[str, ...] = ("UNSEEN",),
    # mail_box: List[
    #             Literal[],
    # mail_status: List[
    #             Literal[
    #                 "all",
    #                 "unseen"
    #                 ]
    #                 ] = "unseen"
) -> list[EmailMessage]:

    app_session.logger = create_logger(name="organizer", file_name="organizer")

    with context_imap_connection(organizer) as mail:
        # list all mailboxes
        mailboxes = list_mailboxes(mail)

        for box in mailboxes:
            status, _ = mail.select(box, readonly=True)
            emails = fetch_mails_from_mailbox(mail, box)

        # if status != "OK":
        #     raise RuntimeError("Could not select INBOX.")

        # status, messages = mail.search(None, "UNSEEN")

        # if status != "OK":
        #     raise RuntimeError("Could not search for unseen emails.")

        # email_ids = messages[0].split()
        # app_session.logger.info(
        #     "Found %s unread emails.",
        #     len(email_ids),
        # )

        # for email_id in email_ids:  # [:10]:
        #     status, data = mail.fetch(
        #         email_id,
        #         "(BODY.PEEK[])",     # w/o changing status
        #     )

        #     if status != "OK"or not data:
        #         app_session.logger.warning(
        #             "Could not fetch email ID %s.",
        #             email_id.decode(errors="replace"),
        #         )
        #         continue

        #     raw_email = next(
        #         (
        #             item[1]
        #             for item in data
        #             if isinstance(item, tuple)
        #             and isinstance(item[1], bytes)
        #         ),
        #         None,
        #     )

        #     if raw_email is None:
        #         app_session.logger.warning(
        #             "No message content found for email ID %r.",
        #             email_id,
        #         )
        #         continue

        #     message = BytesParser(policy=policy.default).parsebytes(raw_email)

        #     subject = message.get("Subject", "(kein Betreff)")
        #     sender = message.get("From", "(unbekannter Absender)")
        #     send_date = get_sent_datetime(message).strftime("%d.%m.%Y %H:%M:%S %z")
        #     receive_date = parse_internal_date()

        #     print(f"{sender}: {subject}")
        # print(f"Von: {item['sender']}")
        # print(f"Betreff: {item['subject']}")
        # print(f"Gesendet: {item['sent_at']}")
        # print(f"Servereingang: {item['received_at']}")
        # print("-" * 60)

    return


# folders = list_mailboxes(mail)

#     for folder in folders:
# folder["type"] = detect_mailbox_type(folder["flags"])
#         print(
#             f"Name: {folder['name']}\n"
# f"Type: {folder['type']}\n"
#             f"Flags: {folder['flags']}\n"
#             f"Delimiter: {folder['delimiter']}\n"
#         )

# if __name__ == "__main__":
#     fetch_mails()

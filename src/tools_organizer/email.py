## email.py
# import
# from email import policy
# from email.parser import BytesParser

from src.core.config import organizer_env_vars as organizer
from src.core.logger import create_logger
from src.core.memory import app_session
from src.utils.email_helper import context_imap_connection


def fetch_mails():

    app_session.logger = create_logger(name="organizer", file_name="organizer")

    with context_imap_connection(organizer) as mail:
        status, _ = mail.select("INBOX")

        emails = fetch_unseen_mails(mail)

        for item in emails:
            print(f"Von: {item['sender']}")
            print(f"Betreff: {item['subject']}")
            print(f"Gesendet: {item['sent_at']}")
            print(f"Servereingang: {item['received_at']}")
            print("-" * 60)

        # if status != "OK":
        #     raise RuntimeError("Could not select INBOX.")

        # status, messages = mail.search(None, "UNSEEN")
        # if status != "OK":
        #     raise RuntimeError("Could not search mailbox for unseen mails.")

        # email_ids = messages[0].split()

        # app_session.logger.info(
        #     "Found %s unread emails.",
        #     len(email_ids),
        #     )

        # for email_id in email_ids:
        #     status, data = mail.fetch(email_id, "(BODY.PEEK[])")    # w/o changing status
        #     # mail.fetch(email_id, "(RFC822)")      # changing status
        #     if status != "OK" or not data:
        #         app_session.logger.warning(
        #             "Could not fetch email ID %s.",
        #             email_id.decode(errors="replace"),
        #         )
        #         continue

        #     # raw_email = data[0][1]
        #     raw_email = next(
        #                 (
        #                 item[1]
        #                 for item in data
        #                 if isinstance(item, tuple)
        #                 and isinstance(item[1], bytes)
        #                 ),
        #                 None
        #                 )

        #     if raw_email is None:
        #         app_session.logger.warning(
        #                 "No message content found for email ID %r.",
        #                 email_id,
        #                 )
        #         continue

        #     message = BytesParser(
        #                     policy=policy.default
        #                 ).parsebytes(raw_email)

        #     subject = message.get("Subject", "(kein Betreff)")
        #     sender = message.get("From", "(unbekannter Absender)")
        #     send_date = get_sent_datetime(message).strftime("%d.%m.%Y %H:%M:%S %z")
        #     receive_date = parse_internal_date()

        #     # for item in emails:
        #     print(f"Von: {item['sender']}")
        #     print(f"Betreff: {item['subject']}")
        #     print(f"Gesendet: {item['sent_at']}")
        #     print(f"Servereingang: {item['received_at']}")
        #     print("-" * 60)
        #     # print(
        #     f"{sender} (time: {date if date is not None else 'unknown'}):\n"
        #     f"-> {subject}\n"
        #     )

    # return


# folders = list_mailboxes(mail)

#     for folder in folders:
# folder["type"] = detect_mailbox_type(folder["flags"])
#         print(
#             f"Name: {folder['name']}\n"
# f"Type: {folder['type']}\n"
#             f"Flags: {folder['flags']}\n"
#             f"Delimiter: {folder['delimiter']}\n"
#         )

if __name__ == "__main__":
    fetch_mails()

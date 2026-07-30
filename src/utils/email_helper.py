from __future__ import annotations

import imaplib
import re
from contextlib import contextmanager

# from getpass import getpass
# from send_msg import send
from datetime import datetime
from email.utils import parsedate_to_datetime

# from email.message import EmailMessage
# import email
from functools import wraps
from typing import Any

from imapclient.imap_utf7 import decode as decode_imap_utf7

from src.core.memory import app_session


# @wraps        # contextlib
def deco_mail_connection(func):

    @wraps(func)
    def wrapper(organizer, *args, **kwargs):
        # port = 465
        # context = ssl.create_default_context()
        # mail = smtplib.SMTP_SSL(organizer.email_server, port, context=context)
        mail = imaplib.IMAP4_SSL(organizer.email_server)  # "imap.gmail.com")

        """
        create_default_context() from the ssl module
        """

        mail.login(organizer.email_address, organizer.email_pw)
        try:
            if app_session.logger:
                app_session.logger.info(
                    "Connected to IMAP server '%s' as '%s'.",
                    organizer.email_server,
                    organizer.email_address,
                )

            return func(
                mail,
                organizer,
                *args,
                **kwargs,
            )

        finally:
            mail.logout()

            if app_session.logger:
                app_session.logger.info("IMAP connection closed.")

    return wrapper


def get_sent_datetime(message) -> datetime | None:
    date_header = message.get("Date")

    if not date_header:
        return None

    try:
        return parsedate_to_datetime(date_header)
    except (TypeError, ValueError, OverflowError):
        return None


# def send(msg, sender_email, password, debug=True):
#     if debug:
#         smtp_server = "localhost"
#         port = 8025
#         with smtplib.SMTP(smtp_server, port) as server:
#             server.send_message(msg)

#     else:
#         smtp_server = "smtp.gmail.com"
#         port = 465
#         # password = getpass("Type your password and press enter: ")

#         context = ssl.create_default_context()
#         with smtplib.SMTP_SSL(
#             	smtp_server,
#                 port,
#                 # context=context
#         	) as smtp:
#             smtp.ehlo()
#             smtp.starttls(context=context)
#             smtp.ehlo()
#             smtp.login(sender_email, password)
#             smtp.send_message(msg)


"""
# contact_details in csv, then read_lines() -> extract Infos

with open("contacts.csv") as file:
    reader = csv.reader(file)
    next(reader)  # Skip header row
    for name, email, grade in reader:
        msg = EmailMessage()
        msg["to"] = f"{name} <{email}>"
        msg["from"] = f"Me <{sender_email}>"
        msg["Subject"] = "Your grade"
        msg.set_content(f"Congratulations, {name}, you got a {grade}.")

        send(msg, sender_email)
"""

# from email.headerregistry import Address

# sender = Address(
# 	display_name="Me",
# 	addr_spec=sender_email,
# 	username="",
# 	domain=""
# 	)


# def build_plain_email():
# 	# Build Email Message
# 	msg = EmailMessage()
# 	msg["to"] = receiver_email  # as iterator, e.g. [receiver_1, receiver_2]
# 	msg["cc"] = cc_receiver_email
# 	msg["bcc"] = bcc_receiver_email
# 	msg["from"] = sender_email
# 	msg["reply-to"] = reply_email
# 	msg["subject"] = "Test Message"
# 	msg.set_content("This is a test message")

# 	#add e.g. text as html
# 	msg.add_alternative(html, subtype="html")

# 	return msg


# attachment_file = Path("smiley-small.jpg")

# def add_attachment(msg, attachment_file):

# 	with open(attachment_file, "rb") as attachment:
#     		# Add attachment to message
#     		msg.add_attachment(
#         		attachment.read(),
#         		maintype="image",
#         		subtype="jpeg",
#         		filename=attachment_file.name,
#     			)

# 	return msg

# # Send message
# send(msg, sender_email)

###############################

# @contextmanager
# def context_smtp_connection(organizer):

#     context = ssl.create_default_context()

#     with smtplib.SMTP_SSL(
#         organizer.smtp_server,
#         organizer.smtp_port,
#         context=context,
#     ) as smtp:
#         smtp.login(
#             organizer.email_address,
#             organizer.email_pw,
#         )
#         yield smtp

#         if app_session.logger:
#         	app_session.logger.info(
#                     "Connected to IMAP server '%s' as '%s'.",
#                     organizer.email_server,
#                     organizer.email_address,
#                     )
#     	try:
#         	yield smtp


MAILBOX_PATTERN = re.compile(
    r"^\((?P<flags>.*?)\)\s+"
    r'(?P<delimiter>NIL|"(?:[^"\\]|\\.)*")\s+'
    r"(?P<name>.+)$"
)


def list_mailboxes(mail) -> list[dict[str, Any]]:
    """
    Return all available IMAP mailboxes with their attributes.

    Example return value:
    [
        {
            "name": "INBOX",
            "flags": ["\\HasNoChildren"],
            "delimiter": "/",
        },
        {
            "name": "Gesendet",
            "flags": ["\\HasNoChildren", "\\Sent"],
            "delimiter": "/",
        },
    ]
    """
    status, rows = mail.list()

    if status != "OK":
        raise RuntimeError(f"Could not retrieve mailbox list: status={status!r}")

    mailboxes: list[dict[str, Any]] = []

    for row in rows or []:
        if not isinstance(row, bytes):
            continue

        decoded = row.decode("ascii", errors="replace")
        # decode_imap_utf7(row)
        match = MAILBOX_PATTERN.match(decoded)

        if match is None:
            # Ungewöhnliche Serverantwort nicht stillschweigend verlieren
            mailboxes.append(
                {
                    "name": decoded,
                    "flags": [],
                    "delimiter": None,
                    "type": detect_mailbox_type(flags),
                    "raw_name": "n.a.",  # match.group("name"),
                    "raw": decoded,
                }
            )
            continue

        flags_text = match.group("flags").strip()
        flags = flags_text.split() if flags_text else []

        delimiter_raw = match.group("delimiter")
        delimiter = None if delimiter_raw == "NIL" else delimiter_raw.strip('"')

        raw_name = match.group("name").strip()  # .strip('"')

        if len(raw_name) >= 2 and raw_name.startswith('"') and raw_name.endswith('"'):
            raw_name = raw_name[1:-1]

        try:
            name = decode_imap_utf7(raw_name.encode("ascii"))
        except (UnicodeEncodeError, UnicodeDecodeError, ValueError) as exc:
            app_session.logger.warning(
                "Could not decode IMAP mailbox name %r: %s",
                raw_name,
                exc,
            )
            name = raw_name

        mailboxes.append(
            {
                "name": name,
                "flags": flags,
                "delimiter": delimiter,
                "type": detect_mailbox_type(flags),
                "raw_name": raw_name,
                "raw": decoded,
            }
        )

    #         @dataclass
    # class Mailbox:
    #     name: str
    #     flags: list[str]
    #     mailbox_type: str | None
    #     delimiter: str | None
    #     raw_name: str
    return mailboxes


SPECIAL_USE_FLAGS = {
    "\\Sent": "sent",
    "\\Drafts": "drafts",
    "\\Trash": "trash",
    "\\Junk": "junk",
    "\\Archive": "archive",
    "\\All": "all",
    "\\Flagged": "flagged",
    "\\Important": "important",
}


def detect_mailbox_type(flags: list[str]) -> str | None:
    for flag in flags:
        mailbox_type = SPECIAL_USE_FLAGS.get(flag)
        if mailbox_type is not None:
            return mailbox_type

    return None


import re

INTERNAL_DATE_PATTERN = re.compile(rb'INTERNALDATE "([^"]+)"')


def parse_internal_date(fetch_metadata: bytes) -> datetime | None:
    match = INTERNAL_DATE_PATTERN.search(fetch_metadata)

    if match is None:
        return None

    value = match.group(1).decode("ascii", errors="replace")

    try:
        return datetime.strptime(
            value,
            "%d-%b-%Y %H:%M:%S %z",
        )
    except ValueError:
        return None


def fetch_unseen_mails(mail) -> list[dict]:
    status, messages = mail.search(None, "UNSEEN")

    if status != "OK":
        raise RuntimeError("Could not search for unseen emails.")

    results = []

    for email_id in messages[0].split():
        status, data = mail.fetch(
            email_id,
            "(INTERNALDATE BODY.PEEK[])",
        )

        if status != "OK":
            continue

        metadata = None
        raw_email = None

        for item in data:
            if not isinstance(item, tuple):
                continue

            if isinstance(item[0], bytes):
                metadata = item[0]

            if isinstance(item[1], bytes):
                raw_email = item[1]

        if raw_email is None:
            continue

        message = BytesParser(policy=policy.default).parsebytes(raw_email)

        date_header = message.get("Date")

        try:
            sent_at = parsedate_to_datetime(date_header) if date_header else None
        except (TypeError, ValueError, OverflowError):
            sent_at = None

        received_at = parse_internal_date(metadata) if metadata is not None else None

        results.append(
            {
                "imap_id": email_id.decode(),
                "subject": message.get(
                    "Subject",
                    "(kein Betreff)",
                ),
                "sender": message.get(
                    "From",
                    "(unbekannter Absender)",
                ),
                "sent_at": sent_at,
                "received_at": received_at,
                "message": message,
            }
        )

    return results


@contextmanager
def context_imap_connection(organizer):

    address = organizer.email_rf_address
    pw = organizer.email_rf_pw

    mail = imaplib.IMAP4_SSL(organizer.imap_server)

    mail.login(
        address,
        pw,
    )

    if app_session.logger:
        app_session.logger.info(
            "Connected to IMAP server '%s' as '%s'.",
            organizer.imap_server,
            address,
        )
    try:
        yield mail

    finally:
        mail.logout()

        if app_session.logger:
            app_session.logger.info("IMAP connection closed.")

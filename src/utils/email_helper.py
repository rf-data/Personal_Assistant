## email_helper.py
# import
from __future__ import annotations
from collections.abc import Iterable  # Callable,
from typing import Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup as bs
import imaplib
from imapclient.imap_utf7 import decode as decode_imap_utf7
from datetime import datetime
import re
from contextlib import contextmanager

# from getpass import getpass
# from send_msg import send
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from email.message import EmailMessage as ParsedEmailMessage
# from email.message import EmailMessage
# from functools import wraps

from src.core.memory import app_session
from src.model_organizer.model_email import Mailbox, EmailMessage


@contextmanager
def context_imap_connection(organizer):

    mail = imaplib.IMAP4_SSL(organizer.imap_server)

    mail.login(
        organizer.email_address,
        organizer.email_pw,
    )

    if app_session.logger:
        app_session.logger.info(
            "Connected to IMAP server '%s' as '%s'.",
            organizer.imap_server,
            organizer.email_address,
        )
    try:
        yield mail

    finally:
        mail.logout()


MAILBOX_PATTERN = re.compile(
    r"^\((?P<flags>.*?)\)\s+"
    r'(?P<delimiter>NIL|"(?:[^"\\]|\\.)*")\s+'
    r"(?P<name>.+)$"
)


def list_mailboxes(mail) -> list[Mailbox]:
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

        decoded = row.decode("utf-8", errors="replace")
        match = MAILBOX_PATTERN.match(decoded)

        if match is None:
            # Ungewöhnliche Serverantwort nicht stillschweigend verlieren
            mailboxes.append(
                Mailbox(name=decoded, flags=[], delimiter=None, raw_name="n.a.")
            )
            continue

        flags_text = match.group("flags").strip()
        flags = flags_text.split() if flags_text else []

        delimiter_raw = match.group("delimiter")
        delimiter = None if delimiter_raw == "NIL" else delimiter_raw.strip('"')

        raw_name = match.group("name").strip()
        # name = match.group("name").strip().strip('"')
        if raw_name.startswith('"') and raw_name.endswith('"'):
            raw_name = raw_name[1:-1]

        name = decode_imap_utf7(raw_name.encode("ascii"))

        mailboxes.append(
            Mailbox(
                name=name,
                flags=flags,
                delimiter=delimiter,
                raw_name=raw_name,  # decoded,
            )
        )

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


def quote_imap_mailbox(name: str) -> str:
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def get_sent_datetime(message) -> datetime | None:
    date_header = message.get("Date")

    if not date_header:
        return None

    try:
        return parsedate_to_datetime(date_header)
    except (TypeError, ValueError, OverflowError):
        return None


INTERNAL_DATE_PATTERN = re.compile(rb'INTERNALDATE "([^"]+)"')


def parse_internal_date(fetch_metadata: bytes) -> datetime | None:
    match = INTERNAL_DATE_PATTERN.search(fetch_metadata)

    if match is None:
        return None

    try:
        return datetime.strptime(
            match.group(1).decode("ascii"),
            "%d-%b-%Y %H:%M:%S %z",
        )
    except ValueError:
        return None


def get_mailbox_status(mail, mailbox: Mailbox):
    # status, messages = mail.search(mailbox)
    imap_name = quote_imap_mailbox(mailbox.raw_name)

    status, data = mail.select(imap_name, readonly=True)

    if status != "OK":
        raise RuntimeError(f"Could not select mailbox {mailbox.name!r}.")
    mailbox.total_messages = int(data[0])

    status, data = mail.search(None, "UNSEEN")
    mailbox.unread_messages = len(data[0].split())
    if status != "OK":
        raise RuntimeError("Could not search unread mails.")

    app_session.logger.info(
        "Found %s total and %s unseen emails",
        mailbox.total_messages,
        mailbox.unread_messages,
    )
    return mailbox


def filter_mails(
    mails: Iterable[EmailMessage],
    keyword: str,
    field: str,
    *,
    case_sensitive: bool = False,
) -> list[EmailMessage]:

    allowed_fields = {
        "subject",
        "sender_name",
        "sender_email",
        "body_plain",
        "body_html",
    }

    if field not in allowed_fields:
        raise ValueError(
            f"Unsupported field {field!r}. Allowed fields: {sorted(allowed_fields)}"
        )

    search_term = keyword if case_sensitive else keyword.casefold()

    matches: list[EmailMessage] = []

    for message in mails:
        value = getattr(message, field, None)

        if value is None:
            continue

        text = str(value)

        if not case_sensitive:
            text = text.casefold()

        if search_term in text:
            matches.append(message)

    return matches


# def select_mails(
#     mails: Iterable[EmailMessage],
#     predicate: Callable[[EmailMessage], bool],
# ) -> list[EmailMessage]:
#     return [
#         mail
#         for mail in mails
#         if predicate(mail)
#     ]

# --> selected = select_mails(
#     mails,
#     lambda item: (
#         item.sender_email is not None
#         and item.sender_email.endswith("@example.com")
#         and item.subject is not None
#         and "rechnung" in item.subject.casefold()
#     ),
# )


def search_mail_uids(
    mail: imaplib.IMAP4_SSL, mailbox: Mailbox, criteria: tuple[str, ...] = ("UNSEEN",)
) -> list[str]:

    status, _ = mail.select(
        mailbox.raw_name,
        readonly=True,
    )

    if status != "OK":
        raise RuntimeError(f"Could not select mailbox {mailbox.name!r}.")

    status, messages = mail.uid(
        "SEARCH",
        None,
        *criteria,
    )

    if status != "OK":
        raise RuntimeError(
            f"Could not search mailbox {mailbox.name!r} with criteria {criteria!r}."
        )

    if not messages or not messages[0]:
        return []

    return [uid.decode("ascii") for uid in messages[0].split()]


def parse_sender(message) -> tuple[str | None, str | None]:
    sender_header = message.get("From", "")
    sender_name, sender_email = parseaddr(sender_header)

    return (
        sender_name or None,
        sender_email or None,
    )


def extract_bodies(
    message: ParsedEmailMessage,
) -> tuple[str | None, str | None]:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    if message.is_multipart():
        for part in message.walk():
            content_disposition = part.get_content_disposition()

            if content_disposition == "attachment":
                continue

            content_type = part.get_content_type()

            try:
                content = part.get_content()
            except (LookupError, UnicodeDecodeError):
                continue

            if not isinstance(content, str):
                continue

            if content_type == "text/plain":
                plain_parts.append(content)

            elif content_type == "text/html":
                html_parts.append(content)

    else:
        try:
            content = message.get_content()
        except (LookupError, UnicodeDecodeError):
            content = None

        if isinstance(content, str):
            if message.get_content_type() == "text/html":
                html_parts.append(content)
            else:
                plain_parts.append(content)

    body_plain = "\n".join(plain_parts).strip() if plain_parts else None

    body_html = "\n".join(html_parts).strip() if html_parts else None

    return body_plain, body_html


def is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)

    return parsed.scheme in {"http", "https"}


# def extract_html_links(html: str | None) -> list[str]:
#     if not html:
#         return []

#     soup = bs(html, "html.parser")
#     links: list[str] = []

#     for tag in soup.find_all("a", href=True):
#         href = tag.get("href")

#         if isinstance(href, str) and is_allowed_url(href):
#             links.append(href)

#     return list(dict.fromkeys(links))


def extract_html_links(
    html: str | None,
) -> list[str]:
    if not html:
        return []

    soup = bs(html, "html.parser")
    links: list[str] = []

    for tag in soup.find_all("a", href=True):
        href = tag.get("href")

        if isinstance(href, str) and is_allowed_url(href):
            links.append(href)

    return list(dict.fromkeys(links))


URL_PATTERN = re.compile(
    r"https?://[^\s<>\"]+",
    flags=re.IGNORECASE,
)


def extract_plain_links(
    text: str | None,
) -> list[str]:
    if not text:
        return []

    return list(
        dict.fromkeys(match.rstrip(".,);]") for match in URL_PATTERN.findall(text))
    )


def extract_links(
    message: EmailMessage,
) -> EmailMessage:

    message.links_plain = extract_plain_links(message.body_plain)
    # links_plain = [*, ]

    message.links_html = extract_html_links(message.body_html)
    # if links_plain:
    #     message.links_plain = list(dict.fromkeys(links_plain))

    #     # for link in links_plain:
    #     #     app_session.logger()
    # else:
    #     message.links_plain = []

    # message.links_html = list(dict.fromkeys(links_html)) if links_html else []

    return message


def fetch_mails_from_mailbox(
    mail: imaplib.IMAP4_SSL,
    mailbox: Mailbox,
    criteria: tuple[str, ...] = ("UNSEEN",),
) -> list[EmailMessage]:

    # (1) find relevant UIDs
    uids = search_mail_uids(
        mail,
        mailbox,
        criteria=criteria,
    )

    # (2) load respective mails as read-only
    results: list[EmailMessage] = []

    for uid in uids:
        status, data = mail.uid(
            "FETCH",
            uid,
            "(INTERNALDATE FLAGS BODY.PEEK[])",
        )

        if status != "OK" or not data:
            app_session.logger.warning(
                "Could not fetch email UID %s.",
                uid,
            )
            continue

        # if status != "OK":
        #     raise RuntimeError("Could not search for unseen emails.")

        # (3) extract meta data + raw mail
        metadata: bytes | None = None
        raw_email: bytes | None = None

        for item in data:
            if not isinstance(item, tuple):
                continue

            if len(item) >= 1 and isinstance(item[0], bytes):
                metadata = item[0]

            if len(item) >= 2 and isinstance(item[1], bytes):
                raw_email = item[1]

        if raw_email is None:
            app_session.logger.warning(
                "No message content found for UID %s.",
                uid,
            )
            continue

        # (4) parse RFC mail
        parsed_message = BytesParser(policy=policy.default).parsebytes(raw_email)

        # (5) extract meta data
        sent_at = get_sent_datetime(parsed_message)

        received_at = parse_internal_date(metadata) if metadata is not None else None

        sender_name, sender_email = parse_sender(parsed_message)

        # (6) extract text / html
        body_plain, body_html = extract_bodies(parsed_message)

        # (7) create DataObject
        message = EmailMessage(
            uid=int(uid),
            message_id=parsed_message.get("Message-ID"),  # email_id.decode(),
            subject=parsed_message.get(
                "Subject",
                # "(kein Betreff)",
            ),
            sender_name=sender_name,
            sender_email=sender_email,
            # message.get(
            #     "From",
            #     "(unbekannter Absender)"
            #     ),
            sent_at=sent_at,
            received_at=received_at,
            body_plain=body_plain,
            body_html=body_html,
        )

        # (8) add extractd raw links
        message = extract_links(message)

        results.append(message)

    return results


# @wraps        # contextlib
# def deco_mail_connection(func):

#     @wraps(func)
#     def wrapper(organizer, *args, **kwargs):
#         # port = 465
#         # context = ssl.create_default_context()
#         # mail = smtplib.SMTP_SSL(organizer.email_server, port, context=context)
#         mail = imaplib.IMAP4_SSL(organizer.email_server)  # "imap.gmail.com")

#         """
#         create_default_context() from the ssl module
#         """

#         mail.login(organizer.email_address, organizer.email_pw)
#         try:
#             if app_session.logger:
#                 app_session.logger.info(
#                     "Connected to IMAP server '%s' as '%s'.",
#                     organizer.email_server,
#                     organizer.email_address,
#                 )

#             return func(
#                 mail,
#                 organizer,
#                 *args,
#                 **kwargs,
#             )

#         finally:
#             mail.logout()

#             if app_session.logger:
#                 app_session.logger.info("IMAP connection closed.")

#     return wrapper


# # import smtplib
# # import ssl
# # from getpass import getpass
# # from send_msg import send
# # from email.message import EmailMessage


# # def send(msg, sender_email, debug=True):
# #     if debug:
# #         smtp_server = "localhost"
# #         port = 8025
# #         with smtplib.SMTP(smtp_server, port) as server:
# #             server.send_message(msg)

# #     else:
# #         smtp_server = "smtp.gmail.com"
# #         port = 465
# #         password = getpass("Type your password and press enter: ")

# #         context = ssl.create_default_context()
# #         with smtplib.SMTP_SSL(
# #             	smtp_server,
# # 		port,
# # 		# context=context
# #         	) as smtp:
# #             	smtp.ehlo()
# #         	smtp.starttls(context=context)
# #         	smtp.ehlo()
# # 		smtp.login(sender_email, password)
# #             	smtp.send_message(msg)


# # """
# # # contact_details in csv, then read_lines() -> extract Infos

# # with open("contacts.csv") as file:
# #     reader = csv.reader(file)
# #     next(reader)  # Skip header row
# #     for name, email, grade in reader:
# #         msg = EmailMessage()
# #         msg["to"] = f"{name} <{email}>"
# #         msg["from"] = f"Me <{sender_email}>"
# #         msg["Subject"] = "Your grade"
# #         msg.set_content(f"Congratulations, {name}, you got a {grade}.")

# #         send(msg, sender_email)
# # """

# # from email.headerregistry import Address

# # sender = Address(
# # 	display_name="Me",
# # 	addr_spec=sender_email,
# # 	username="",
# # 	domain=""
# # 	)


# # def build_plain_email():
# # 	# Build Email Message
# # 	msg = EmailMessage()
# # 	msg["to"] = receiver_email  # as iterator, e.g. [receiver_1, receiver_2]
# # 	msg["cc"] = cc_receiver_email
# # 	msg["bcc"] = bcc_receiver_email
# # 	msg["from"] = sender_email
# # 	msg["reply-to"] = reply_email
# # 	msg["subject"] = "Test Message"
# # 	msg.set_content("This is a test message")

# # 	#add e.g. text as html
# # 	msg.add_alternative(html, subtype="html")

# # 	return msg


# # attachment_file = Path("smiley-small.jpg")

# # def add_attachment(msg, attachment_file):

# # 	with open(attachment_file, "rb") as attachment:
# #     		# Add attachment to message
# #     		msg.add_attachment(
# #         		attachment.read(),
# #         		maintype="image",
# #         		subtype="jpeg",
# #         		filename=attachment_file.name,
# #     			)

# # 	return msg

# # # Send message
# # send(msg, sender_email)

# # ###############################

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

#     	if app_session.logger:
#         	app_session.logger.info(
#                     "Connected to IMAP server '%s' as '%s'.",
#                     organizer.email_server,
#                     organizer.email_address,
#                     )
#     	try:
#         	yield smtp


# if app_session.logger:
#     app_session.logger.info("IMAP connection closed.")

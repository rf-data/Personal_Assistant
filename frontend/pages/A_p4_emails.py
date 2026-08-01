## A_p4_emails.py
# imports
import imaplib
import email
import streamlit as st

from src.core.config import organizer_env_vars as organizer
from src.core.logger import create_logger
from src.core.memory import app_session
from src.utils.email_helper import (
    context_imap_connection,
    fetch_unseen_mails,
    list_mailboxes,
)


def show():
    st.header("🏠 Startseite ")
    st.subheader("**E-Mails**")

    st.divider()

    # st.markdown("**Under Construction**")

    # step 1

    "https://realpython.com/ref/stdlib/imaplib/"
    "https://realpython.com/python-send-email/"

    "https://docs.pythonlang.de/3/library/imaplib.html"
    "https://www.w3schools.com/python/ref_module_imaplib.asp"
    """
    Verwendung von imaplib in Python
    imaplib — IMAP4 protocol client — Python 3.13.5 documentation
    https://docs.python.org/3/library/imaplib.html
    How to fetch an email body using imaplib in python? - Stack Overflow
    https://stackoverflow.com/questions/2230037/how-to-fetch-an-email-body-using-imaplib-in-python
    imaplib2 · PyPI
    https://pypi.org/project/imaplib2/
    Das Modul imaplib in Python bietet eine Schnittstelle zur Kommunikation mit IMAP4-Servern und unterstützt eine Vielzahl von IMAP4rev1-Befehlen. Es ermöglicht das Abrufen, Verwalten und Manipulieren von E-Mails auf einem IMAP-Server.

    Grundlegende Funktionen und Klassen

    Das Modul definiert drei Hauptklassen:

    IMAP4: Stellt die Standard-IMAP4-Verbindung her. Standardmäßig wird Port 143 verwendet.

    IMAP4_SSL: Verwendet eine SSL-verschlüsselte Verbindung (Port 993).

    IMAP4_stream: Ermöglicht Verbindungen über einen Unterprozess.

    Beispiel: Verbindung zu einem IMAP-Server und Abrufen von E-Mails

    import imaplib
    import getpass

    # Verbindung zum IMAP-Server herstellen
    server = imaplib.IMAP4_SSL('imap.example.com')
    server.login(getpass.getuser(), getpass.getpass())

    # Postfach auswählen
    server.select('INBOX')

    # Alle Nachrichten abrufen
    status, messages = server.search(None, 'ALL')

    # Nachrichten durchlaufen und Inhalte abrufen
    for num in messages[0].split():
    status, data = server.fetch(num, '(RFC822)')
    print(f'Nachricht {num}:\n{data[0][1].decode("utf-8")}\n')

    # Verbindung schließen
    server.close()
    server.logout()

    ##  Wichtige Methoden
    login(user, password): Authentifiziert den Benutzer.
    select(mailbox='INBOX', readonly=False): Wählt ein Postfach aus.
    search(charset, criterion): Sucht nach Nachrichten basierend auf Kriterien wie FROM, SUBJECT oder ALL.
    fetch(message_set, message_parts): Ruft spezifische Teile einer Nachricht ab, z. B. den Textkörper.
    store(message_set, command, flag_list): Ändert Flags von Nachrichten, z. B. \Seen oder \Deleted.
    expunge(): Entfernt dauerhaft gelöschte Nachrichten.
    logout(): Trennt die Verbindung zum Server.

    ## Fehlerbehandlung
    Das Modul definiert spezifische Ausnahmen:
    IMAP4.error: Allgemeiner Fehler.
    IMAP4.abort: Fehler aufgrund von Serverproblemen.
    IMAP4.readonly: Fehler, wenn ein Postfach schreibgeschützt wird.

    ##  Erweiterte Nutzung
    Für komplexere Anforderungen, wie parallele Verbindungen oder bessere Performance, kann die Bibliothek imaplib2 verwendet werden.
    Sie basiert auf imaplib, unterstützt jedoch Threads und bietet eine optimierte Nutzung von IMAP4-Funktionen.

    Beispiel mit imaplib2

    from imaplib2 import IMAP4_SSL

    # Verbindung herstellen
    server = IMAP4_SSL('imap.example.com')
    server.login('user@example.com', 'password')

    # Postfach auswählen und Nachrichten abrufen
    server.select('INBOX')
    status, messages = server.search(None, 'UNSEEN')

    # Verarbeitung der Nachrichten
    for num in messages[0].split():
        status, data = server.fetch(num, '(RFC822)')
        print(data[0][1].decode('utf-8'))

    server.logout()

    ## Wichtige Hinweise
    Sicherheitsaspekte: Verwenden Sie immer SSL/TLS für sichere Verbindungen.
    UIDs verwenden: Da sich Nachrichten-IDs nach Änderungen im Postfach ändern können, ist es ratsam, UIDs zu verwenden.
    Fehlerbehandlung: Überprüfen Sie stets den Rückgabestatus (OK oder NO), um Fehler zu vermeiden.
    Mit imaplib können Sie effizient E-Mails abrufen und verwalten, wobei die Flexibilität der IMAP4-Protokollbefehle voll ausgeschöpft wird.
    """

    with st.expander("**Mail boxes**"):
        with context_imap_connection(organizer) as mail:
            # list mail box folders
            boxes = list_mailboxes(mail)

            for box in boxes:
                box = get_mailbox_status(mail, box)

                st.write(
                    f"**Name mailbox:**\t{box.name}"
                    f"**Total emails:** \t{box.total_messages}"
                    f"**Unseen emails:** \t{box.unread_messages}"
                    )

        # mail_box = st.pills(label="", option=[])

    # step 2
    # with st.expander(""):
    # emails = [
    #     (f"Mail {idx}", mail) for idx, mail in enumerate(emails)
    # ]  # all (new) mails
    # for idx, mail in emails:
    #     # import email
    #     raw_mail = ""
    #     message = email.message_from_string(raw_mail)
    #     st.write(
    #         f"{idx}:\nSubject: {message['Subject']} \nFrom: {message['From']}"
    #     )  # header

    #     # mail.select("inbox")

    # email_to_respond = st.text_input(
    #     "List emails (as 'Mail idx', sep=", ") for whom AI should prepare a response. "
    # ).split(", ")
    # with context_imap_connection(organizer) as mail:
    #     boxes_all = list_mailboxes(mail)

    #     status, _ = mail.select("INBOX", readonly=True)
    #     if status != "OK":
    #         raise RuntimeError("Could not select INBOX.")

    #     new_mails = fetch_unseen_mails(mail)

    #     st.json(boxes_all)

    #     st.divider()
    #     # for box in boxes_all:

    #     # box_to_see = st.selectbox(
    #     #             label="",
    #     #             options=[b["name"] for b in boxes_all],
    #     #             # default=None
    #     #             )

    # with st.expander("**Unseen Emails**"):
    #     # st.markdown("**Under Construction**")

    #     st.json(new_mails[0])


"""
## TO-DOS
- email filtern nach Absender | Datum | Mailbox
- Information aus gefilterten Mails extrahieren,
  z.B. Links zu Artikeln
"""
# emails = [(f"Mail {idx}",
#            mail) in idx, mail for enumerate(emails)]    # all (new) mails
# for idx, mail in emails:
#     # import email
#     raw_mail = ""
#     message = email.message_from_string(raw_mail)
#     st.write(f"{idx}:\nSubject: {message["Subject"]} \nFrom: {message["From"]})    # header

#     # mail.select("inbox")

# email_to_respond = st.text_input("List emails (as 'Mail idx', sep=",") for whom AI should prepare a response. ").split(", ")


'''
from openai import OpenAI
client = OpenAI()
def classify_email(email_content):
    prompt = f"""
    Classify this email into one category:
    - Urgent
    - Client Request
    - Meeting
    - Information
    - Spam
    Email:
    {email_content}
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response.choices[0].message.content
'''

'''
import smtplib
from email.message import EmailMessage
email = EmailMessage()
email["Subject"] = "Monthly Report"
email["From"] = "your_email@gmail.com"
email["To"] = "client@example.com"
email.set_content("""
Hello,
Please find the attached report.
Best regards
""")
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login("your_email@gmail.com", "your_password")
    smtp.send_message(email)
print("Email sent successfully")
'''

"""
import openai
import whisper
import smtplib
from email.mime.text import MIMEText

# Load Whisper model
model = whisper.load_model("base")

# Transcribe audio
result = model.transcribe("meeting.mp3")
transcript = result["text"]

# Send transcript to GPT
client = openai.OpenAI(api_key="YOUR_API_KEY")

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "system",
            "content": "Summarize the meeting and extract action items."
        },
        {
            "role": "user",
            "content": transcript
        }
    ]
)

summary = response.choices[0].message.content

# Email summary
msg = MIMEText(summary)
msg["Subject"] = "Meeting Summary"
msg["From"] = "team@company.com"
msg["To"] = "staff@company.com"

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login("your_email", "your_password")
    server.send_message(msg)

print("Summary sent successfully.")
"""


'''
import openai

client = openai.OpenAI(api_key="YOUR_API_KEY")

incoming_email = """
Hi team,

Can we move tomorrow's meeting
to Thursday afternoon instead?

Thanks,
Sarah
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "system",
            "content": """
            Write a professional
            and concise email reply.
            """
        },*a
        {
            "role": "user",
            "content": incoming_email
        }
    ]
)

print(response.choices[0].message.content)
'''


"""
# step 1
import imaplib
import email
mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login("your_email@gmail.com", "password")
mail.select("inbox")

# step 2
status, messages = mail.search(None, "UNSEEN")
email_ids = messages[0].split()
for email_id in email_ids:
    _, data = mail.fetch(email_id, "(RFC822)")
    raw_email = data[0][1]

    message = email.message_from_bytes(raw_email)
    print(message["Subject"])

# step 3
"""

"""
Libraries:

imaplib
email
pandas
openai
A simple extraction example:

import email
message = email.message_from_string(raw_email)
sender = message["From"]
subject = message["Subject"]
print(sender)
print(subject)
"""

'''
    from openai import OpenAI

client = OpenAI()

def summarize_email(email_text):

    response = client.responses.create(
        model="gpt-5",
        input=f"""
        Summarize this email.

        {email_text}
        """
    )

    return response.output_text

'''

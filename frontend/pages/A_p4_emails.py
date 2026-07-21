## A_p4_emails.py
# imports
import streamlit as st

"""
Calender

import markdown
import pdfkit
md_content = "# Daily Plan\n- Task 1\n- Task 2"
html_content = markdown.markdown(md_content)
pdfkit.from_string(html_content, "daily_plan.pdf")

"""


def show():
    st.header("🏠 Startseite ")
    st.subheader("**E-Mails**")

    st.divider()

    st.markdown("**Under Construction**")


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
        },
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

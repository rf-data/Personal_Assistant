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

                )
    return wrapper


import smtplib
import ssl
from getpass import getpass
from send_msg import send
from email.message import EmailMessage


def send(msg, sender_email, debug=True):
    if debug:
        smtp_server = "localhost"
        port = 8025
        with smtplib.SMTP(smtp_server, port) as server:
            server.send_message(msg)

    else:
        smtp_server = "smtp.gmail.com"
        port = 465
        password = getpass("Type your password and press enter: ")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            	smtp_server, 	
		port, 
		# context=context
        	) as smtp:
            	smtp.ehlo()
        	smtp.starttls(context=context)
        	smtp.ehlo()
		smtp.login(sender_email, password)
            	smtp.send_message(msg)


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

from email.headerregistry import Address

sender = Address(
	display_name="Me", 
	addr_spec=sender_email,
	username="",
	domain=""
	)


def build_plain_email():
	# Build Email Message
	msg = EmailMessage()
	msg["to"] = receiver_email  # as iterator, e.g. [receiver_1, receiver_2]
	msg["cc"] = cc_receiver_email
	msg["bcc"] = bcc_receiver_email
	msg["from"] = sender_email
	msg["reply-to"] = reply_email
	msg["subject"] = "Test Message"
	msg.set_content("This is a test message")
	
	#add e.g. text as html 
	msg.add_alternative(html, subtype="html")

	return msg


attachment_file = Path("smiley-small.jpg")

def add_attachment(msg, attachment_file):
		
	with open(attachment_file, "rb") as attachment:
    		# Add attachment to message
    		msg.add_attachment(
        		attachment.read(),
        		maintype="image",
        		subtype="jpeg",
        		filename=attachment_file.name,
    			)

	return msg

# Send message
send(msg, sender_email)

############################### 

@contextmanager
def context_smtp_connection(organizer):

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        organizer.smtp_server,
        organizer.smtp_port,
        context=context,
    ) as smtp:
        smtp.login(
            organizer.email_address,
            organizer.email_pw,
        )
        yield smtp
 
    	if app_session.logger:
        	app_session.logger.info(
                    "Connected to IMAP server '%s' as '%s'.",
                    organizer.email_server,
                    organizer.email_address,
                    )
    	try:
        	yield smtp

    	
@contextmanager
def context_imap_connection(organizer):

    mail = imaplib.IMAP4_SSL(
        organizer.email_server
    )

    mail.login(
        organizer.email_address,
        organizer.email_pw,
        )
    
    if app_session.logger:
        app_session.logger.info(
                    "Connected to IMAP server '%s' as '%s'.",
                    organizer.email_server,
                    organizer.email_address,
                    )
    try:
        yield mail

    finally:
        mail.logout()
        
        if app_session.logger:
            app_session.logger.info("IMAP connection closed.")

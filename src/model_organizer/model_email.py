## model_email.py
# import
from typing import List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class Attachment(BaseModel):
    filename: str
    content_type: str
    size: int


class Mailbox(BaseModel):
    name: str
    flags: list[str] = Field(default_factory=list)

    delimiter: str | None
    raw_name: str

    total_messages: int | None = None
    unread_messages: int | None = None


class EmailMessage(BaseModel):
    uid: int  # str

    message_id: str

    # sequence_number: int | None
    subject: str | None

    sender_name: str
    sender_email: EmailStr

    to: list[EmailStr] = Field(default_factory=list)
    cc: list[EmailStr] = Field(default_factory=list)
    in_reply_to: str | None

    sent_at: datetime | None = None
    received_at: datetime | None = None

    body_plain: str | None
    body_html: str | None

    flags: list[str] = Field(default_factory=list)

    attachments: List[Attachment] = Field(default_factory=list)
    # references: list[str] = []
    # labels: list[str] = []

from celery import shared_task
from flask_mail import Message

from app import mail


@shared_task(ignore_result=True, max_retries=3)
def send_email(subject: str, sender: str | tuple[str, str], recipients: list[str | tuple[str, str]], text_body: str,
               html_body: str, attachments=None):
    msg = Message(subject, recipients, text_body, html_body, sender=sender)
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    mail.send(msg)

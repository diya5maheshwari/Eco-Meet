import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Your Gmail account
SENDER_EMAIL = "divyanshiraghav473@gmail.com"

# Gmail App Password (NOT your Gmail password)
APP_PASSWORD = "gixa vybv qtne uipc"


def send_email(receiver_email, meet_link):
    try:
        subject = "EchoMeet Meeting Invitation"

        body = f"""
Hello,

You have been invited to a meeting via EchoMeet.

Join using this link:
{meet_link}

Regards,
EchoMeet Assistant
"""

        # Create email message
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = receiver_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(message)

        print(f"Email sent successfully to {receiver_email}")

    except Exception as e:
        print(f"Error sending email to {receiver_email}: {e}")
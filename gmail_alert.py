import os
import base64
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")


def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_test_email():
    service = get_gmail_service()

    sender = "me"
    recipient = "hbenfraj60@gmail.com"

    subject = "Hazem AI News Trader - Test"
    body = (
        "Gmail Alert Test\n\n"
        "Hazem AI News Trader is connected successfully.\n"
        "This is a test message."
    )

    message = MIMEText(body)
    message["to"] = recipient
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    service.users().messages().send(
        userId=sender,
        body={"raw": raw_message}
    ).execute()

    print("GMAIL TEST SUCCESS")


if __name__ == "__main__":
    send_test_email()
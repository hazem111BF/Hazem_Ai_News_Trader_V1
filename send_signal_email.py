import os
import json
import base64
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
SIGNAL_FILE = os.path.join(BASE_DIR, "latest_signal.json")


def get_gmail_service():
    creds = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        SCOPES
    )

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


def send_signal_email():
    if not os.path.exists(SIGNAL_FILE):
        print("ERROR: latest_signal.json not found")
        return False

    with open(SIGNAL_FILE, "r", encoding="utf-8") as f:
        signal = json.load(f)

    service = get_gmail_service()

    direction = signal.get("direction", "UNKNOWN")
    final_score = signal.get("final_score", "N/A")
    market_score = signal.get("market_score", "N/A")
    news_score = signal.get("news_score", "N/A")
    confidence = signal.get("news_confidence", "N/A")
    reason = signal.get("reason", "N/A")

    subject = f"XAUUSD Signal: {direction}"

    body = f"""Hazem AI News Trader

Asset: XAUUSD
Direction: {direction}

Final Score: {final_score}
Market Score: {market_score}
News Score: {news_score}
News Confidence: {confidence}

Reason:
{reason}

This is an ALERT ONLY.
No automatic trade was executed.
"""

    message = MIMEText(body)
    message["to"] = "hbenfraj60@gmail.com"
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw_message}
    ).execute()

    print("SIGNAL EMAIL SENT SUCCESSFULLY")
    return True


if __name__ == "__main__":
    send_signal_email()
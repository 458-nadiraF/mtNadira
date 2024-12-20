import os
import imaplib
import email
import requests
from email.header import decode_header
from flask import Flask, request, jsonify

# Flask app for Vercel
app = Flask(__name__)

# Email credentials and webhook URL from environment variables
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")  # Default is Gmail IMAP server
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # The URL to send the JSON to

def fetch_email():
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)

        # Select the mailbox to check (e.g., inbox)
        mail.select("inbox")

        # Search for unread emails
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return {"status": "error", "message": "Failed to fetch emails"}

        # Fetch the latest unread email
        email_ids = messages[0].split()
        if not email_ids:
            return {"status": "success", "message": "No unread emails"}

        latest_email_id = email_ids[-1]  # Get the latest email
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        if status != "OK":
            return {"status": "error", "message": "Failed to fetch the latest email"}

        # Parse the email
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                # Decode email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                # Decode email sender
                from_ = msg.get("From")

                # Process email content
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                # Process the body (e.g., "SELL MARUBOZU 0.0031 301")
                if body:
                    result = process_message(body)
                    if result["status"] == "success":
                        send_to_webhook(result["data"])

                # Return processed message (if needed)
                return {
                    "status": "success",
                    "subject": subject,
                    "from": from_,
                    "body": body,
                }

        mail.logout()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def process_message(body):
    try:
        # Split the body by space
        message_parts = body.split()
        if len(message_parts) < 4:
            return {"status": "error", "message": "Invalid message format"}

        # Determine action type based on the first part
        act_type = "ORDER_TYPE_SELL" if message_parts[0] == "SELL" else "ORDER_TYPE_BUY"

        # Extract the remaining data
        marubozu_type = message_parts[1]  # Example: "MARUBOZU"
        price = message_parts[2]  # Example: "0.0031"
        volume = message_parts[3]  # Example: "301"

        # Create the JSON message to send to the webhook
        json_data = {
            "action_type": act_type,
            "marubozu_type": marubozu_type,
            "price": price,
            "volume": volume
        }

        return {"status": "success", "data": json_data}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_to_webhook(data):
    try:
        # Send the data to the specified webhook URL
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code == 200:
            print("Data sent to webhook successfully.")
        else:
            print(f"Failed to send data: {response.status_code}")
    except Exception as e:
        print(f"Error sending data to webhook: {str(e)}")

@app.route("/api/check-email", methods=["GET"])
def check_email():
    result = fetch_email()
    return jsonify(result)

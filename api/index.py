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
                    # Return processed message (if needed)
                        return {
                            "status": "success",
                            "subject": subject,
                            "from": from_,
                            "body": body,
                        }
                    else
                        return {
                            "status": "failed",
                            "subject": subject,
                            "from": from_,
                            "body": body,
                        }

        mail.logout()
    except Exception as e:
        return {"status": "error", "message": str(e)}
def get_account_balance(self,token, account):
        headers = {
            'Accept': 'application/json',
            'auth-token': token 
        }
        
        try:
            get_balance_url=f"https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/{account}/account-information"
            response = requests.get(get_balance_url, headers=headers)
            
            # Check if request was successful
            if response.status_code == 200:
                data = response.json()
                return data.get('balance')  
            else:
                print(f"Error: API request for get balance failed with status code {response.status_code}")
                print(response) 
                return None
                
        except Exception as e:
            print(f"Error fetching balance: {str(e)}")
            return None
def process_message(body):
    try:
        # Split the body by space
        message_parts = body.split(" ")
        if len(message_parts) < 4:
            return {"status": "error", "message": "Invalid message format"}

        # Determine action type based on the first part
        act_type = "ORDER_TYPE_SELL" if message_parts[0] == "SELL" else "ORDER_TYPE_BUY"

        # Extract the remaining data
        //marubozu_type = message_parts[1]  # Example: "MARUBOZU"
        price = message_parts[3]  # Example: "0.0031"
        volume = message_parts[2]  # Example: "301"

        # accountName=received_json.get('account')
        accountStr=f'ACCOUNT_ID'
        tokenStr=f'METAAPI_TOKEN'
        account=os.getenv(accountStr)
        token=os.getenv(tokenStr)
        # a=0
        # if accountName=="masnur":
        #     if symbol[-1]!='m' :
        #         symbol=f'{symbol}m'
        #     a=1
        # else:
        #     if symbol[-1]=='m' :
        #         symbol=symbol[0:-1]
        balance=self.get_account_balance(token, account)
        # Define the API endpoint where you want to forward the request
        forward_url = f"https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/{account}/trade"  # Replace with your actual API endpoint
        balance2= float(balance) 
        buy_json={
            "symbol": "XAUUSDm",
            "actionType": act_type,
            "volume": round(volume*balance2, 2),
            "stopLoss": 0,
            "takeProfit": float(price),
            "takeProfitUnits": "RELATIVE_POINTS"
        }
        
        headers = {
            'Accept': 'application/json',
            'auth-token':token,
            'Content-Type':'application/json'
            # Add any other required headers here
        }
        
        response = requests.post(
            forward_url,
            json=buy_json,
            headers=headers
        )
        # Create the JSON message to send to the webhook


        return {"status": "success", "data": buy_data}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.route("/api/check-email", methods=["GET"])
def check_email():
    result = fetch_email()
    return jsonify(result)

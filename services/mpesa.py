import os
import base64
import requests
from datetime import datetime

MPESA_CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.environ.get("MPESA_SHORTCODE", "174379")  # Safaricom's shared sandbox shortcode
MPESA_PASSKEY = os.environ.get("MPESA_PASSKEY")
MPESA_CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL") 

# Sandbox base URL — swap to https://api.safaricom.co.ke for production
MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"


class MpesaService:
    @staticmethod
    def _get_access_token():
        """Fetch an OAuth token using the Consumer Key/Secret."""
        url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
        response.raise_for_status()
        return response.json()["access_token"]

    @staticmethod
    def _generate_password(timestamp):
        """Base64(Shortcode + Passkey + Timestamp), as required by Safaricom."""
        raw = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
        return base64.b64encode(raw.encode()).decode()

    @staticmethod
    def stk_push(phone_number, amount, account_reference, description="Farmart order payment"):
        """
        Sends an STK Push prompt to the buyer's phone.
        Returns the Safaricom response dict, which includes CheckoutRequestID.
        """
        access_token = MpesaService._get_access_token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = MpesaService._generate_password(timestamp)

        url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount), 
            "PartyA": phone_number,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": account_reference,
            "TransactionDesc": description,
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
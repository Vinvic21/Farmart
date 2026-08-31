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
    def _format_phone(phone_number):
        """
        Safaricom's Daraja API only accepts MSISDN in the 2547XXXXXXXX /
        2541XXXXXXXX format (12 digits, no '+', no leading 0). Buyers type
        numbers as 07..., +2547..., 2547... etc, so normalize here — this
        was the main cause of STK pushes silently failing.
        """
        if not phone_number:
            raise ValueError("Phone number is required for M-Pesa payment")

        digits = "".join(ch for ch in str(phone_number) if ch.isdigit())

        if digits.startswith("254") and len(digits) == 12:
            return digits
        if digits.startswith("0") and len(digits) == 10:
            return "254" + digits[1:]
        if digits.startswith("7") or digits.startswith("1"):
            if len(digits) == 9:
                return "254" + digits

        raise ValueError(
            f"Invalid phone number '{phone_number}'. Use a Safaricom number like 0712345678."
        )

    @staticmethod
    def _get_access_token():
        """Fetch an OAuth token using the Consumer Key/Secret."""
        if not MPESA_CONSUMER_KEY or not MPESA_CONSUMER_SECRET:
            raise RuntimeError(
                "M-Pesa is not configured: set MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET"
            )
        url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(
            url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET), timeout=15
        )
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
        if not MPESA_CALLBACK_URL:
            raise RuntimeError("M-Pesa is not configured: set MPESA_CALLBACK_URL")

        formatted_phone = MpesaService._format_phone(phone_number)
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
            "PartyA": formatted_phone,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": formatted_phone,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": account_reference,
            "TransactionDesc": description,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        result = response.json()

        if result.get("ResponseCode") not in (0, "0"):
            raise RuntimeError(result.get("ResponseDescription") or "STK push was rejected")

        return result
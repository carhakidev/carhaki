import hmac
import hashlib
import requests
from django.conf import settings

PAYSTACK_BASE = "https://api.paystack.co"


def initialize_transaction(email: str, amount_ngn: int, reference: str, callback_url: str) -> dict:
    """
    Initiate a Paystack transaction.
    amount_ngn is in Naira — converts to kobo internally.
    Returns the full Paystack response dict.
    """
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "amount": amount_ngn * 100,  # kobo
        "reference": reference,
        "callback_url": callback_url,
        "currency": "NGN",
    }
    response = requests.post(
        f"{PAYSTACK_BASE}/transaction/initialize",
        json=payload,
        headers=headers,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def verify_transaction(reference: str) -> dict:
    """
    Verify a Paystack transaction by reference.
    Returns the full Paystack response dict.
    """
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    response = requests.get(
        f"{PAYSTACK_BASE}/transaction/verify/{reference}",
        headers=headers,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Validate Paystack webhook HMAC-SHA512 signature.
    Paystack sends the digest in the x-paystack-signature header.
    """
    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

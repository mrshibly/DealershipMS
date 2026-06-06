import os
import asyncio
import httpx
from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/1")
result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

celery_app = Celery(
    "dms_worker",
    broker=broker_url,
    backend=result_backend
)

# Optional config
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Dhaka",
    enable_utc=True,
)

async def _send_ssl_commerz_sms(phone: str, message: str, api_key: str, sender_id: str):
    """
    Async function to interact with the SMS Gateway API
    Using placeholder API structure based on typical SSL Wireless implementation.
    """
    url = "https://smsplus.sslwireless.com/api/v3/send-sms"
    payload = {
        "api_token": api_key,
        "sid": sender_id,
        "msisdn": phone,
        "sms": message,
        "csms_id": os.urandom(8).hex()
    }
    
    async with httpx.AsyncClient() as client:
        # In a real scenario we'd do:
        # response = await client.post(url, json=payload)
        # response.raise_for_status()
        # For development without a real API key, we simulate:
        print(f"[CELERY] Mock SMS sent to {phone}: '{message}' (Sender: {sender_id})")
        await asyncio.sleep(1) # simulate network delay

@celery_app.task(name="app.worker.send_sms_task", bind=True, max_retries=3)
def send_sms_task(self, phone: str, message: str, api_key: str, sender_id: str):
    """
    Celery task to send SMS asynchronously.
    """
    try:
        # Celery tasks are synchronous, so we run the async httpx call in an event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_send_ssl_commerz_sms(phone, message, api_key, sender_id))
        return {"status": "success", "phone": phone}
    except Exception as exc:
        # Retry with exponential backoff if network fails
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

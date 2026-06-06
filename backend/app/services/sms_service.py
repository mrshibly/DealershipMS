from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.setting_service import get_all_settings
from app.worker import send_sms_task

async def send_sms_notification(db: AsyncSession, phone: str, message: str) -> bool:
    """
    Fetches the SMS configuration from settings and triggers the Celery worker.
    """
    if not phone or not message:
        return False

    settings = await get_all_settings(db)
    
    # Check if SMS is globally enabled
    sms_enabled = settings.get("sms_enabled", "false").lower() == "true"
    if not sms_enabled:
        print(f"SMS is disabled in settings. Skipping message to {phone}.")
        return False

    api_key = settings.get("sms_api_key")
    sender_id = settings.get("sms_sender_id")

    if not api_key or not sender_id:
        print("SMS configuration missing (api_key or sender_id).")
        return False

    # Dispatch to Celery worker immediately
    send_sms_task.delay(phone, message, api_key, sender_id)
    return True

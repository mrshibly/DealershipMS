from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting
from app.schemas.setting import SettingUpdate

async def get_all_settings(db: AsyncSession) -> Dict[str, str]:
    """Returns all settings as a key-value dictionary."""
    result = await db.execute(select(Setting))
    return {s.key: s.value for s in result.scalars().all()}

async def update_settings(db: AsyncSession, settings_data: Dict[str, str]) -> Dict[str, str]:
    """Updates or creates multiple settings."""
    for key, value in settings_data.items():
        result = await db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            db.add(Setting(key=key, value=value))
            
    await db.commit()
    return await get_all_settings(db)

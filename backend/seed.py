"""
Seed script — creates default roles and Super Admin user.
Run once after initial migration:
  python seed.py

Default credentials:
  Email:    admin@dms.local
  Password: Admin@1234   ← CHANGE THIS after first login!
"""
import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add app to path
sys.path.insert(0, ".")

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.role import (
    DEFAULT_PERMISSIONS_ADMIN,
    DEFAULT_PERMISSIONS_DSR,
    DEFAULT_PERMISSIONS_STAFF,
    DEFAULT_PERMISSIONS_SUPER_ADMIN,
    Role,
)
from app.models.user import User

settings = get_settings()


async def seed() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSession_ = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSession_() as session:
        async with session.begin():
            # --- Roles ---
            role_data = [
                ("Super Admin", DEFAULT_PERMISSIONS_SUPER_ADMIN),
                ("Admin", DEFAULT_PERMISSIONS_ADMIN),
                ("Staff", DEFAULT_PERMISSIONS_STAFF),
                ("DSR", DEFAULT_PERMISSIONS_DSR),
            ]

            roles: dict[str, Role] = {}
            for name, perms in role_data:
                from sqlalchemy import select
                result = await session.execute(select(Role).where(Role.name == name))
                existing = result.scalar_one_or_none()
                if existing:
                    print(f"  [SKIP] Role '{name}' already exists")
                    roles[name] = existing
                else:
                    role = Role(name=name, permissions=perms)
                    session.add(role)
                    await session.flush()
                    roles[name] = role
                    print(f"  [OK]   Role '{name}' created")

            # --- Super Admin user ---
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == "admin@dms.local")
            )
            existing_user = result.scalar_one_or_none()
            if existing_user:
                print("  [SKIP] Super Admin user already exists")
            else:
                admin = User(
                    name="Super Admin",
                    email="admin@dms.local",
                    password_hash=hash_password("Admin@1234"),
                    role_id=roles["Super Admin"].id,
                    language="bn",
                    is_active=True,
                )
                session.add(admin)
                print("  [OK]   Super Admin user created: admin@dms.local / Admin@1234")

    await engine.dispose()
    print("\nSeed complete! IMPORTANT: Change admin password after first login.")


if __name__ == "__main__":
    asyncio.run(seed())

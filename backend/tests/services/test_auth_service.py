import pytest
from app.services.user_service import get_password_hash
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_password_hashing():
    password = "secret_password"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert pwd_context.verify(password, hashed)
    assert not pwd_context.verify("wrong_password", hashed)

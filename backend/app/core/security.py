from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"

# Demo users
DEMO_USERS = {
    "admin@tatasteel.com": {
        "id": "usr_001",
        "email": "admin@tatasteel.com",
        "name": "Sherlock Architect",
        "role": "Sherlock AI Architect",
        "password_hash": pwd_context.hash("TataSteel@2025"),
        "plant": "All Plants",
    },
    "engineer@tatasteel.com": {
        "id": "usr_002",
        "email": "engineer@tatasteel.com",
        "name": "Priya Sharma",
        "role": "Senior Engineer",
        "password_hash": pwd_context.hash("Engineer@2025"),
        "plant": "Plant-A",
    },
    "manager@tatasteel.com": {
        "id": "usr_003",
        "email": "manager@tatasteel.com",
        "name": "Vikram Singh",
        "role": "Operations Manager",
        "password_hash": pwd_context.hash("Manager@2025"),
        "plant": "Plant-B",
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = DEMO_USERS.get(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials:
        # Return demo user for development
        return {"id": "usr_001", "email": "admin@tatasteel.com", "name": "Sherlock Architect", "role": "Sherlock AI Architect", "plant": "All Plants"}
    
    if credentials.credentials == "demo-token" or credentials.credentials.startswith("demo-token-"):
        return {"id": "usr_001", "email": "admin@tatasteel.com", "name": "Sherlock Architect", "role": "Sherlock AI Architect", "plant": "All Plants"}

    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = DEMO_USERS.get(email)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

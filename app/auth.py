import datetime
from typing import Optional
import jwt
from fastapi import Request, HTTPException, status
from app.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_DAYS,
    INTERVIEW_PASSWORD,
    INTERVIEW_ALT_PASSWORD,
)

COOKIE_NAME = "interview_token"


def verify_password(plain_password: str) -> bool:
    if not plain_password:
        return False
    stripped = plain_password.strip()
    return stripped == INTERVIEW_PASSWORD.strip() or stripped == INTERVIEW_ALT_PASSWORD.strip()


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


def get_token_from_request(request: Request) -> Optional[str]:
    # Check Cookie first
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token

    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    # Check query param (useful for downloads or quick testing)
    query_token = request.query_params.get("token")
    if query_token:
        return query_token

    return None


def get_current_user(request: Request) -> dict:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with the access password.",
        )
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again.",
        )
    return payload


def is_authenticated(request: Request) -> bool:
    token = get_token_from_request(request)
    if not token:
        return False
    payload = verify_token(token)
    return payload is not None

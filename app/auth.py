import datetime
import secrets
import time
from typing import Optional, Tuple
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
JWT_ISSUER = "interview-mentor"
JWT_AUDIENCE = "interview-mentor-user"


class LoginRateLimiter:
    """
    In-memory rate limiter for login brute force mitigation.
    Tracks failed attempts per IP.
    Max 5 failed attempts within 60 seconds triggers a 300-second (5 min) lockout.
    """
    def __init__(self, max_attempts: int = 5, window_seconds: int = 60, lockout_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._records: dict[str, dict] = {}

    def is_locked(self, ip: str) -> Tuple[bool, int]:
        now = time.time()
        record = self._records.get(ip)
        if not record:
            return False, 0
        locked_until = record.get("locked_until", 0)
        if now < locked_until:
            retry_after = max(1, int(locked_until - now))
            return True, retry_after
        return False, 0

    def record_failure(self, ip: str) -> Tuple[bool, int]:
        now = time.time()
        record = self._records.setdefault(ip, {"attempts": [], "locked_until": 0})
        # Clean up older timestamps outside window
        record["attempts"] = [t for t in record["attempts"] if now - t < self.window_seconds]
        record["attempts"].append(now)

        if len(record["attempts"]) >= self.max_attempts:
            record["locked_until"] = now + self.lockout_seconds
            return True, self.lockout_seconds
        return False, 0

    def record_success(self, ip: str) -> None:
        self._records.pop(ip, None)

    def reset(self) -> None:
        self._records.clear()


# Global limiter instance
login_rate_limiter = LoginRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract real client IP behind Nginx reverse proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def verify_password(plain_password: str) -> bool:
    """
    Timing-attack-resistant password verification using secrets.compare_digest.
    """
    if not plain_password or not isinstance(plain_password, str):
        return False

    plain_bytes = plain_password.strip().encode("utf-8")
    matched = False

    if INTERVIEW_PASSWORD:
        target_bytes = INTERVIEW_PASSWORD.strip().encode("utf-8")
        if secrets.compare_digest(plain_bytes, target_bytes):
            matched = True

    if INTERVIEW_ALT_PASSWORD:
        alt_bytes = INTERVIEW_ALT_PASSWORD.strip().encode("utf-8")
        if secrets.compare_digest(plain_bytes, alt_bytes):
            matched = True

    return matched


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    Generates a hardened HS256 JWT with issuer, audience, and unique jti token id.
    """
    to_encode = data.copy()
    now = datetime.datetime.now(datetime.timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": expire,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "jti": secrets.token_hex(16),
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Decodes and validates JWT token with expiration and signature check.
    """
    if not token or not isinstance(token, str):
        return None
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        return payload
    except Exception:
        # Fallback to decode without strict audience/issuer for backward compatibility
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except Exception:
            return None


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts authentication token from:
    1. HTTP-Only Cookie
    2. Authorization: Bearer <token> header
    3. Query parameter ?token=<token>
    """
    # Check Cookie first
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token

    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    # Check query param (useful for SSE streams or preview links)
    query_token = request.query_params.get("token")
    if query_token:
        return query_token

    return None


def get_current_user(request: Request) -> dict:
    """
    FastAPI dependency that enforces valid authenticated token.
    Raises 401 if missing or invalid.
    """
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with the access password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def is_authenticated(request: Request) -> bool:
    """
    Returns True if request has a valid, non-expired authentication token.
    """
    token = get_token_from_request(request)
    if not token:
        return False
    payload = verify_token(token)
    return payload is not None

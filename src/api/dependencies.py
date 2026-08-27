from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session, sessionmaker

from src.core.database import build_engine, build_session_factory
from src.platform.auth.models import AuthSession
from src.platform.auth.service import validate_session
from src.platform.identity.models import User


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker:
    # Deliberately lazy: importing the FastAPI app must not open or require a DB connection.
    return build_session_factory(build_engine())


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
    scheme, _, token = authorization.partition(" ")
    if scheme.casefold() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
    return token


@dataclass(frozen=True)
class AuthContext:
    token: str
    auth_session: AuthSession
    user: User


def get_auth_context(
    token: str = Depends(bearer_token),
    db: Session = Depends(get_db),
) -> AuthContext:
    result = validate_session(db, token)
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
    auth_session, user = result
    return AuthContext(token=token, auth_session=auth_session, user=user)

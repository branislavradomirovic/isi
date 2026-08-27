from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.core.config import get_settings


class Base(DeclarativeBase):
    pass


def build_engine():
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


def build_session_factory(engine=None):
    engine = engine or build_engine()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)

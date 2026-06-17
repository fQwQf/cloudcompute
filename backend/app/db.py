from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


settings = get_settings()


def patch_opengauss_version_parser() -> None:
    original = PGDialect_psycopg2._get_server_version_info

    def parse_version(self, connection):  # type: ignore[no-untyped-def]
        try:
            return original(self, connection)
        except AssertionError as exc:
            version_text = connection.exec_driver_sql("select version()").scalar() or ""
            if "openGauss" not in version_text:
                raise exc
            return (9, 2)

    PGDialect_psycopg2._get_server_version_info = parse_version


patch_opengauss_version_parser()


class Base(DeclarativeBase):
    pass


engine_kwargs = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    if ":memory:" in settings.database_url:
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

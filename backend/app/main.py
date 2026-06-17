from contextlib import asynccontextmanager
from time import sleep

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.routes import analytics, insights, operations, resources, system, usage
from app.services import seed_demo_data

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    last_error: Exception | None = None
    for _ in range(30):
        try:
            init_db()
            if settings.auto_seed:
                db = SessionLocal()
                try:
                    seed_demo_data(db)
                finally:
                    db.close()
            last_error = None
            break
        except OperationalError as exc:
            last_error = exc
            sleep(2)
    if last_error:
        raise last_error
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(system.router, prefix=settings.api_prefix)
    app.include_router(resources.router, prefix=settings.api_prefix)
    app.include_router(usage.router, prefix=settings.api_prefix)
    app.include_router(analytics.router, prefix=settings.api_prefix)
    app.include_router(insights.router, prefix=settings.api_prefix)
    app.include_router(operations.router, prefix=settings.api_prefix)
    return app


app = create_app()

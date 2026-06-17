from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AnalyticsOverview, SnapshotRead
from app.services import build_analytics_overview, recompute_snapshot

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_overview(
    days: int = Query(default=30, ge=7, le=90), db: Session = Depends(get_db)
) -> AnalyticsOverview:
    return build_analytics_overview(db, days=days)


@router.post("/recompute", response_model=SnapshotRead)
def run_recompute(db: Session = Depends(get_db)):
    return recompute_snapshot(db, generated_by="api")

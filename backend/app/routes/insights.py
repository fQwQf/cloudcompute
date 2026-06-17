from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import InsightsDashboard, SimulationRequest, SimulationResponse
from app.services import build_insights_dashboard, simulate_optimization

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/dashboard", response_model=InsightsDashboard)
def get_insights_dashboard(db: Session = Depends(get_db)) -> InsightsDashboard:
    return build_insights_dashboard(db)


@router.post("/recompute", response_model=InsightsDashboard)
def recompute_insights(db: Session = Depends(get_db)) -> InsightsDashboard:
    return build_insights_dashboard(db, persist=True)


@router.post("/simulate", response_model=SimulationResponse)
def simulate_cost(payload: SimulationRequest) -> SimulationResponse:
    return simulate_optimization(payload)

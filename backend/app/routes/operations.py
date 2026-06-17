from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AlertRead, AlertSummary, ImportResult
from app.services import acknowledge_alert, generate_ops_report_markdown, get_alert_summary, import_usage_csv, recompute_alerts

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/alerts", response_model=AlertSummary)
def list_alerts(db: Session = Depends(get_db)) -> AlertSummary:
    return get_alert_summary(db)


@router.post("/alerts/recompute", response_model=AlertSummary)
def run_alert_rules(db: Session = Depends(get_db)) -> AlertSummary:
    return recompute_alerts(db)


@router.post("/alerts/{alert_id}/ack", response_model=AlertRead)
def ack_alert(alert_id: str, db: Session = Depends(get_db)) -> AlertRead:
    alert = acknowledge_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")
    return AlertRead.model_validate(alert)


@router.post("/import/usage-csv", response_model=ImportResult)
async def upload_usage_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ImportResult:
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="only csv files are supported")
    return import_usage_csv(db, await file.read())


@router.get("/reports/weekly.md")
def download_weekly_report(db: Session = Depends(get_db)) -> Response:
    content = generate_ops_report_markdown(db)
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=cloudcostlab-weekly-report.md"},
    )

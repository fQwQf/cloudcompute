import csv
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditEvent, CloudResource
from app.schemas import AuditRead, Message, SeedRequest
from app.services import seed_demo_data

router = APIRouter(tags=["system"])


@router.get("/health", response_model=Message)
def health() -> Message:
    return Message(message="ok")


@router.post("/demo/seed", response_model=Message)
def seed_demo(payload: SeedRequest, db: Session = Depends(get_db)) -> Message:
    seed_demo_data(db, reset=payload.reset)
    return Message(message="demo data ready")


@router.get("/audit-log", response_model=list[AuditRead])
def list_audit_log(limit: int = 30, db: Session = Depends(get_db)) -> list[AuditEvent]:
    query = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    return list(db.scalars(query).all())


@router.get("/export/resources.csv")
def export_resources(db: Session = Depends(get_db)) -> StreamingResponse:
    rows = db.scalars(select(CloudResource).order_by(CloudResource.created_at.desc())).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["id", "name", "provider", "region", "resource_type", "owner", "status", "monthly_budget"]
    )
    for row in rows:
        writer.writerow(
            [
                row.id,
                row.name,
                row.provider,
                row.region,
                row.resource_type,
                row.owner,
                row.status,
                row.monthly_budget,
            ]
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=cloud-resources.csv"},
    )

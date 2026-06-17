from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models import CloudResource, UsageRecord
from app.schemas import UsageCreate, UsageRead
from app.services import create_usage_record, to_usage_read

router = APIRouter(prefix="/usage-records", tags=["usage"])


@router.get("", response_model=list[UsageRead])
def list_usage_records(
    resource_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(default=100, le=500, ge=1),
    db: Session = Depends(get_db),
) -> list[UsageRead]:
    query = select(UsageRecord).options(joinedload(UsageRecord.resource)).order_by(
        UsageRecord.record_date.desc(), UsageRecord.created_at.desc()
    )
    if resource_id:
        query = query.where(UsageRecord.resource_id == resource_id)
    if start_date:
        query = query.where(UsageRecord.record_date >= start_date)
    if end_date:
        query = query.where(UsageRecord.record_date <= end_date)
    records = db.scalars(query.limit(limit)).all()
    return [to_usage_read(record) for record in records]


@router.post("", response_model=UsageRead, status_code=status.HTTP_201_CREATED)
def add_usage_record(payload: UsageCreate, db: Session = Depends(get_db)) -> UsageRead:
    resource = db.get(CloudResource, payload.resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="resource not found")
    record = create_usage_record(db, payload)
    record.resource = resource
    return to_usage_read(record)

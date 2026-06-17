from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CloudResource
from app.schemas import ResourceCreate, ResourceRead, ResourceUpdate
from app.services import create_resource, delete_resource, update_resource

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=list[ResourceRead])
def list_resources(
    q: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    provider: str | None = None,
    region: str | None = None,
    limit: int = Query(default=100, le=500, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[CloudResource]:
    query = select(CloudResource).order_by(CloudResource.created_at.desc())
    if q:
        like = f"%{q}%"
        query = query.where(
            CloudResource.name.ilike(like)
            | CloudResource.owner.ilike(like)
            | CloudResource.resource_type.ilike(like)
        )
    if status_filter:
        query = query.where(CloudResource.status == status_filter)
    if provider:
        query = query.where(CloudResource.provider == provider)
    if region:
        query = query.where(CloudResource.region == region)
    return list(db.scalars(query.offset(offset).limit(limit)).all())


@router.post("", response_model=ResourceRead, status_code=status.HTTP_201_CREATED)
def add_resource(payload: ResourceCreate, db: Session = Depends(get_db)) -> CloudResource:
    return create_resource(db, payload)


@router.get("/{resource_id}", response_model=ResourceRead)
def get_resource(resource_id: str, db: Session = Depends(get_db)) -> CloudResource:
    resource = db.get(CloudResource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="resource not found")
    return resource


@router.put("/{resource_id}", response_model=ResourceRead)
def edit_resource(
    resource_id: str, payload: ResourceUpdate, db: Session = Depends(get_db)
) -> CloudResource:
    resource = db.get(CloudResource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="resource not found")
    return update_resource(db, resource, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_resource(resource_id: str, db: Session = Depends(get_db)) -> None:
    resource = db.get(CloudResource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="resource not found")
    delete_resource(db, resource)

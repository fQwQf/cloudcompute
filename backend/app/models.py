from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def uuid_str() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class CloudResource(Base):
    __tablename__ = "cloud_resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="Huawei Cloud")
    region: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    owner: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    monthly_budget: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    usage_records: Mapped[list["UsageRecord"]] = relationship(
        back_populates="resource", cascade="all, delete-orphan"
    )


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    resource_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_resources.id"), nullable=False, index=True
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    cpu_core_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    memory_gb_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    storage_gb_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    network_gb: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    carbon_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    utilization_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    resource: Mapped[CloudResource] = relationship(back_populates="usage_records")


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    resource_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_utilization_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    carbon_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    top_region: Mapped[str] = mapped_column(String(80), nullable=False, default="-")
    risk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generated_by: Mapped[str] = mapped_column(String(40), nullable=False, default="api")


class CloudInsight(Base):
    __tablename__ = "cloud_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    resource_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    estimated_saving: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class CloudAlert(Base):
    __tablename__ = "cloud_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    rule_key: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    resource_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ResourceBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    provider: str = Field(default="Huawei Cloud", max_length=40)
    region: str = Field(max_length=80)
    resource_type: str = Field(max_length=40)
    owner: str = Field(max_length=80)
    status: str = Field(default="active", pattern="^(active|paused|retired)$")
    monthly_budget: float = Field(ge=0)


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    provider: str | None = Field(default=None, max_length=40)
    region: str | None = Field(default=None, max_length=80)
    resource_type: str | None = Field(default=None, max_length=40)
    owner: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, pattern="^(active|paused|retired)$")
    monthly_budget: float | None = Field(default=None, ge=0)


class ResourceRead(ResourceBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsageBase(BaseModel):
    resource_id: str
    record_date: date
    cpu_core_hours: float = Field(ge=0)
    memory_gb_hours: float = Field(ge=0)
    storage_gb_hours: float = Field(ge=0)
    network_gb: float = Field(ge=0)
    utilization_score: float = Field(ge=0, le=100)
    estimated_cost: float | None = Field(default=None, ge=0)
    carbon_kg: float | None = Field(default=None, ge=0)


class UsageCreate(UsageBase):
    pass


class UsageRead(BaseModel):
    id: str
    resource_id: str
    resource_name: str | None = None
    record_date: date
    cpu_core_hours: float
    memory_gb_hours: float
    storage_gb_hours: float
    network_gb: float
    estimated_cost: float
    carbon_kg: float
    utilization_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrendPoint(BaseModel):
    date: date
    cost: float
    carbon_kg: float
    avg_utilization_score: float


class DimensionPoint(BaseModel):
    label: str
    value: float


class BudgetRisk(BaseModel):
    resource_id: str
    name: str
    owner: str
    used_cost: float
    monthly_budget: float
    budget_ratio: float


class SnapshotRead(BaseModel):
    id: str
    snapshot_time: datetime
    resource_count: int
    active_count: int
    total_cost: float
    avg_utilization_score: float
    carbon_kg: float
    top_region: str
    risk_count: int
    generated_by: str

    model_config = ConfigDict(from_attributes=True)


class InsightRead(BaseModel):
    id: str
    category: str
    severity: str
    title: str
    description: str
    resource_id: str | None
    resource_name: str | None
    impact_score: float
    estimated_saving: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForecastPoint(BaseModel):
    date: date
    predicted_cost: float
    predicted_carbon_kg: float


class AnomalyPoint(BaseModel):
    date: date
    resource_name: str
    actual_cost: float
    baseline_cost: float
    deviation_ratio: float
    reason: str


class InsightsDashboard(BaseModel):
    generated_at: datetime
    forecast: list[ForecastPoint]
    projected_30d_cost: float
    projected_30d_carbon_kg: float
    total_budget: float
    budget_pressure: float
    saving_potential: float
    risk_level: str
    recommendations: list[InsightRead]
    anomalies: list[AnomalyPoint]


class SimulationRequest(BaseModel):
    cpu_core_hours: float = Field(ge=0)
    memory_gb_hours: float = Field(ge=0)
    storage_gb_hours: float = Field(ge=0)
    network_gb: float = Field(ge=0)
    utilization_score: float = Field(ge=1, le=100)
    target_utilization_score: float = Field(default=75, ge=1, le=100)
    days: int = Field(default=30, ge=1, le=365)


class SimulationResponse(BaseModel):
    current_period_cost: float
    optimized_period_cost: float
    saving: float
    saving_ratio: float
    current_carbon_kg: float
    optimized_carbon_kg: float
    carbon_reduction_kg: float
    recommendation: str


class AlertRead(BaseModel):
    id: str
    rule_key: str
    alert_type: str
    severity: str
    title: str
    description: str
    resource_id: str | None
    resource_name: str | None
    metric_value: float
    threshold_value: float
    status: str
    created_at: datetime
    acknowledged_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AlertSummary(BaseModel):
    total: int
    open_count: int
    critical_count: int
    high_count: int
    alerts: list[AlertRead]


class ImportResult(BaseModel):
    imported_count: int
    created_resources: int
    skipped_rows: int
    errors: list[str]


class AnalyticsOverview(BaseModel):
    resource_count: int
    active_count: int
    total_cost: float
    avg_utilization_score: float
    carbon_kg: float
    top_region: str
    risk_count: int
    trend: list[TrendPoint]
    cost_by_resource: list[DimensionPoint]
    cost_by_region: list[DimensionPoint]
    budget_risks: list[BudgetRisk]
    latest_snapshot: SnapshotRead | None = None


class AuditRead(BaseModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: str | None
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SeedRequest(BaseModel):
    reset: bool = False


class Message(BaseModel):
    message: str

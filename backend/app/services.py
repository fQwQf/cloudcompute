import csv
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from io import StringIO
from math import sqrt

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import (
    AnalyticsSnapshot,
    AuditEvent,
    CloudAlert,
    CloudInsight,
    CloudResource,
    UsageRecord,
    uuid_str,
)
from app.schemas import (
    AlertRead,
    AlertSummary,
    AnomalyPoint,
    AnalyticsOverview,
    BudgetRisk,
    DimensionPoint,
    ForecastPoint,
    ImportResult,
    InsightRead,
    InsightsDashboard,
    ResourceCreate,
    ResourceUpdate,
    SimulationRequest,
    SimulationResponse,
    SnapshotRead,
    TrendPoint,
    UsageCreate,
    UsageRead,
)


def compute_estimated_cost(payload: UsageCreate) -> float:
    return round(
        payload.cpu_core_hours * 0.045
        + payload.memory_gb_hours * 0.012
        + payload.storage_gb_hours * 0.0006
        + payload.network_gb * 0.08,
        2,
    )


def compute_carbon_kg(payload: UsageCreate) -> float:
    energy_kwh = (
        payload.cpu_core_hours * 0.035
        + payload.memory_gb_hours * 0.004
        + payload.storage_gb_hours * 0.0002
    )
    return round(energy_kwh * 0.581, 2)


def add_audit_event(
    db: Session, event_type: str, entity_type: str, message: str, entity_id: str | None = None
) -> None:
    db.add(
        AuditEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
        )
    )


def create_resource(db: Session, payload: ResourceCreate) -> CloudResource:
    resource = CloudResource(**payload.model_dump())
    db.add(resource)
    db.flush()
    add_audit_event(db, "resource_created", "cloud_resource", f"新增资源 {resource.name}", resource.id)
    db.commit()
    db.refresh(resource)
    return resource


def update_resource(db: Session, resource: CloudResource, payload: ResourceUpdate) -> CloudResource:
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(resource, key, value)
    resource.updated_at = datetime.now(UTC)
    add_audit_event(db, "resource_updated", "cloud_resource", f"更新资源 {resource.name}", resource.id)
    db.commit()
    db.refresh(resource)
    return resource


def delete_resource(db: Session, resource: CloudResource) -> None:
    add_audit_event(db, "resource_deleted", "cloud_resource", f"删除资源 {resource.name}", resource.id)
    db.delete(resource)
    db.commit()


def create_usage_record(db: Session, payload: UsageCreate) -> UsageRecord:
    estimated_cost = payload.estimated_cost
    if estimated_cost is None:
        estimated_cost = compute_estimated_cost(payload)

    carbon_kg = payload.carbon_kg
    if carbon_kg is None:
        carbon_kg = compute_carbon_kg(payload)

    data = payload.model_dump(exclude={"estimated_cost", "carbon_kg"})
    record = UsageRecord(**data, estimated_cost=estimated_cost, carbon_kg=carbon_kg)
    db.add(record)
    db.flush()
    add_audit_event(
        db,
        "usage_recorded",
        "usage_record",
        f"写入 {record.record_date.isoformat()} 用量，成本 {record.estimated_cost:.2f}",
        record.id,
    )
    db.commit()
    db.refresh(record)
    return record


def to_usage_read(record: UsageRecord) -> UsageRead:
    return UsageRead(
        id=record.id,
        resource_id=record.resource_id,
        resource_name=record.resource.name if record.resource else None,
        record_date=record.record_date,
        cpu_core_hours=record.cpu_core_hours,
        memory_gb_hours=record.memory_gb_hours,
        storage_gb_hours=record.storage_gb_hours,
        network_gb=record.network_gb,
        estimated_cost=record.estimated_cost,
        carbon_kg=record.carbon_kg,
        utilization_score=record.utilization_score,
        created_at=record.created_at,
    )


def build_analytics_overview(db: Session, days: int = 30) -> AnalyticsOverview:
    start_date = date.today() - timedelta(days=days - 1)
    resources = db.scalars(select(CloudResource)).all()
    records = db.scalars(select(UsageRecord).where(UsageRecord.record_date >= start_date)).all()

    resource_by_id = {resource.id: resource for resource in resources}
    resource_count = len(resources)
    active_count = sum(1 for resource in resources if resource.status == "active")
    total_cost = round(sum(record.estimated_cost for record in records), 2)
    carbon_kg = round(sum(record.carbon_kg for record in records), 2)
    avg_utilization_score = round(
        sum(record.utilization_score for record in records) / len(records), 1
    ) if records else 0.0

    trend_map: dict[date, dict[str, float]] = defaultdict(lambda: {"cost": 0.0, "carbon": 0.0, "util": 0.0, "count": 0})
    resource_costs: dict[str, float] = defaultdict(float)
    region_costs: dict[str, float] = defaultdict(float)

    for record in records:
        bucket = trend_map[record.record_date]
        bucket["cost"] += record.estimated_cost
        bucket["carbon"] += record.carbon_kg
        bucket["util"] += record.utilization_score
        bucket["count"] += 1

        resource = resource_by_id.get(record.resource_id)
        label = resource.name if resource else record.resource_id
        region = resource.region if resource else "unknown"
        resource_costs[label] += record.estimated_cost
        region_costs[region] += record.estimated_cost

    trend: list[TrendPoint] = []
    for index in range(days):
        current = start_date + timedelta(days=index)
        bucket = trend_map[current]
        count = bucket["count"] or 1
        trend.append(
            TrendPoint(
                date=current,
                cost=round(bucket["cost"], 2),
                carbon_kg=round(bucket["carbon"], 2),
                avg_utilization_score=round(bucket["util"] / count, 1) if bucket["count"] else 0.0,
            )
        )

    cost_by_resource = [
        DimensionPoint(label=label, value=round(value, 2))
        for label, value in sorted(resource_costs.items(), key=lambda item: item[1], reverse=True)[:6]
    ]
    cost_by_region = [
        DimensionPoint(label=label, value=round(value, 2))
        for label, value in sorted(region_costs.items(), key=lambda item: item[1], reverse=True)
    ]
    top_region = cost_by_region[0].label if cost_by_region else "-"

    budget_risks: list[BudgetRisk] = []
    for resource in resources:
        used_cost = round(resource_costs.get(resource.name, 0.0), 2)
        if resource.monthly_budget <= 0:
            continue
        budget_ratio = round(used_cost / resource.monthly_budget, 3)
        if budget_ratio >= 0.8:
            budget_risks.append(
                BudgetRisk(
                    resource_id=resource.id,
                    name=resource.name,
                    owner=resource.owner,
                    used_cost=used_cost,
                    monthly_budget=resource.monthly_budget,
                    budget_ratio=budget_ratio,
                )
            )
    budget_risks.sort(key=lambda item: item.budget_ratio, reverse=True)

    latest_snapshot_model = db.scalars(
        select(AnalyticsSnapshot).order_by(AnalyticsSnapshot.snapshot_time.desc()).limit(1)
    ).first()
    latest_snapshot = SnapshotRead.model_validate(latest_snapshot_model) if latest_snapshot_model else None

    return AnalyticsOverview(
        resource_count=resource_count,
        active_count=active_count,
        total_cost=total_cost,
        avg_utilization_score=avg_utilization_score,
        carbon_kg=carbon_kg,
        top_region=top_region,
        risk_count=len(budget_risks),
        trend=trend,
        cost_by_resource=cost_by_resource,
        cost_by_region=cost_by_region,
        budget_risks=budget_risks[:5],
        latest_snapshot=latest_snapshot,
    )


def recompute_snapshot(db: Session, generated_by: str = "api") -> AnalyticsSnapshot:
    overview = build_analytics_overview(db)
    snapshot = AnalyticsSnapshot(
        resource_count=overview.resource_count,
        active_count=overview.active_count,
        total_cost=overview.total_cost,
        avg_utilization_score=overview.avg_utilization_score,
        carbon_kg=overview.carbon_kg,
        top_region=overview.top_region,
        risk_count=overview.risk_count,
        generated_by=generated_by,
    )
    db.add(snapshot)
    db.flush()
    add_audit_event(db, "analytics_recomputed", "analytics_snapshot", "重新生成分析快照", snapshot.id)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def _recent_records(db: Session, days: int = 30) -> tuple[list[CloudResource], list[UsageRecord]]:
    start_date = date.today() - timedelta(days=days - 1)
    resources = db.scalars(select(CloudResource)).all()
    records = db.scalars(select(UsageRecord).where(UsageRecord.record_date >= start_date)).all()
    return resources, records


def _linear_forecast(values: list[float], count: int = 7) -> list[float]:
    if not values:
        return [0.0] * count
    if len(values) == 1:
        return [values[0]] * count

    n = len(values)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    denominator = sum((x - mean_x) ** 2 for x in xs) or 1
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values, strict=True)) / denominator
    intercept = mean_y - slope * mean_x
    return [max(0.0, intercept + slope * (n + index)) for index in range(count)]


def _build_forecast(records: list[UsageRecord], days: int = 30) -> tuple[list[ForecastPoint], float, float]:
    start_date = date.today() - timedelta(days=days - 1)
    cost_by_day: dict[date, float] = defaultdict(float)
    carbon_by_day: dict[date, float] = defaultdict(float)
    for record in records:
        cost_by_day[record.record_date] += record.estimated_cost
        carbon_by_day[record.record_date] += record.carbon_kg

    costs = [cost_by_day[start_date + timedelta(days=index)] for index in range(days)]
    carbons = [carbon_by_day[start_date + timedelta(days=index)] for index in range(days)]
    forecast_costs = _linear_forecast(costs)
    forecast_carbons = _linear_forecast(carbons)
    tomorrow = date.today() + timedelta(days=1)
    forecast = [
        ForecastPoint(
            date=tomorrow + timedelta(days=index),
            predicted_cost=round(forecast_costs[index], 2),
            predicted_carbon_kg=round(forecast_carbons[index], 2),
        )
        for index in range(7)
    ]

    recent_window = costs[-7:] if len(costs) >= 7 else costs
    recent_carbon = carbons[-7:] if len(carbons) >= 7 else carbons
    projected_30d_cost = round((sum(recent_window) / len(recent_window) * 30) if recent_window else 0, 2)
    projected_30d_carbon = round(
        (sum(recent_carbon) / len(recent_carbon) * 30) if recent_carbon else 0, 2
    )
    return forecast, projected_30d_cost, projected_30d_carbon


def _detect_anomalies(resources: list[CloudResource], records: list[UsageRecord]) -> list[AnomalyPoint]:
    resource_by_id = {resource.id: resource for resource in resources}
    cost_by_resource_day: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for record in records:
        cost_by_resource_day[record.resource_id][record.record_date] += record.estimated_cost

    anomalies: list[AnomalyPoint] = []
    for resource_id, day_costs in cost_by_resource_day.items():
        values = list(day_costs.values())
        if len(values) < 5:
            continue
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        stddev = sqrt(variance)
        threshold = mean + max(stddev * 1.8, mean * 0.35, 8)
        for record_date, actual_cost in day_costs.items():
            if actual_cost <= threshold:
                continue
            resource = resource_by_id.get(resource_id)
            anomalies.append(
                AnomalyPoint(
                    date=record_date,
                    resource_name=resource.name if resource else resource_id,
                    actual_cost=round(actual_cost, 2),
                    baseline_cost=round(mean, 2),
                    deviation_ratio=round((actual_cost - mean) / mean, 2) if mean else 0,
                    reason="当日成本显著高于近 30 天基线，建议检查弹性扩容、批处理任务或异常流量。",
                )
            )
    anomalies.sort(key=lambda item: item.deviation_ratio, reverse=True)
    return anomalies[:6]


def _make_insight(
    category: str,
    severity: str,
    title: str,
    description: str,
    resource: CloudResource | None,
    impact_score: float,
    estimated_saving: float,
) -> CloudInsight:
    return CloudInsight(
        id=uuid_str(),
        category=category,
        severity=severity,
        title=title,
        description=description,
        resource_id=resource.id if resource else None,
        resource_name=resource.name if resource else None,
        impact_score=round(impact_score, 1),
        estimated_saving=round(estimated_saving, 2),
        status="open",
        created_at=datetime.now(UTC),
    )


def _recommend_insights(
    resources: list[CloudResource],
    records: list[UsageRecord],
    anomalies: list[AnomalyPoint],
    projected_30d_cost: float,
) -> list[CloudInsight]:
    records_by_resource: dict[str, list[UsageRecord]] = defaultdict(list)
    for record in records:
        records_by_resource[record.resource_id].append(record)

    insights: list[CloudInsight] = []
    for resource in resources:
        resource_records = records_by_resource.get(resource.id, [])
        used_cost = sum(record.estimated_cost for record in resource_records)
        carbon_kg = sum(record.carbon_kg for record in resource_records)
        avg_utilization = (
            sum(record.utilization_score for record in resource_records) / len(resource_records)
            if resource_records
            else 0
        )
        if used_cost > 40 and avg_utilization < 45:
            saving = used_cost * 0.28
            insights.append(
                _make_insight(
                    "rightsizing",
                    "high",
                    f"{resource.name} 存在降配空间",
                    f"近 30 天平均利用率约 {avg_utilization:.1f}%，但成本为 {used_cost:.2f} 元。建议调小规格、启用自动伸缩或合并低峰任务。",
                    resource,
                    88 - avg_utilization,
                    saving,
                )
            )
        if resource.monthly_budget > 0 and used_cost / resource.monthly_budget >= 0.8:
            insights.append(
                _make_insight(
                    "budget",
                    "critical" if used_cost / resource.monthly_budget >= 1 else "high",
                    f"{resource.name} 接近预算上限",
                    f"已消耗 {used_cost:.2f} 元，月预算 {resource.monthly_budget:.2f} 元。建议设置预算告警并排查高成本时段。",
                    resource,
                    min(100, used_cost / resource.monthly_budget * 100),
                    max(0, used_cost - resource.monthly_budget * 0.75),
                )
            )
        if carbon_kg > 45:
            insights.append(
                _make_insight(
                    "carbon",
                    "medium",
                    f"{resource.name} 碳排放偏高",
                    f"近 30 天估算碳排放 {carbon_kg:.1f} kg。建议迁移非实时任务到低峰运行，或优先使用更高利用率实例。",
                    resource,
                    min(90, carbon_kg),
                    used_cost * 0.08,
                )
            )
        if resource.status == "paused" and used_cost > 20:
            insights.append(
                _make_insight(
                    "lifecycle",
                    "medium",
                    f"{resource.name} 处于暂停状态但仍有成本",
                    "建议检查关联存储、快照、弹性 IP 等残留资源，避免暂停后继续产生费用。",
                    resource,
                    66,
                    used_cost * 0.18,
                )
            )

    if projected_30d_cost > 0:
        total_budget = sum(resource.monthly_budget for resource in resources)
        if total_budget and projected_30d_cost / total_budget > 0.85:
            insights.append(
                _make_insight(
                    "forecast",
                    "critical",
                    "未来 30 天成本预测逼近总预算",
                    f"按最近 7 天趋势估算，未来 30 天成本约 {projected_30d_cost:.2f} 元，建议优先处理高成本资源和异常日期。",
                    None,
                    min(100, projected_30d_cost / total_budget * 100),
                    projected_30d_cost * 0.12,
                )
            )

    for anomaly in anomalies[:3]:
        insights.append(
            _make_insight(
                "anomaly",
                "high",
                f"{anomaly.resource_name} 出现成本尖峰",
                f"{anomaly.date.isoformat()} 成本 {anomaly.actual_cost:.2f} 元，高于基线 {anomaly.baseline_cost:.2f} 元。",
                None,
                min(100, 55 + anomaly.deviation_ratio * 20),
                max(0, anomaly.actual_cost - anomaly.baseline_cost),
            )
        )

    insights.sort(key=lambda item: (item.severity != "critical", -item.impact_score))
    return insights[:8]


def build_insights_dashboard(db: Session, persist: bool = False) -> InsightsDashboard:
    resources, records = _recent_records(db)
    forecast, projected_30d_cost, projected_30d_carbon = _build_forecast(records)
    anomalies = _detect_anomalies(resources, records)
    insight_models = _recommend_insights(resources, records, anomalies, projected_30d_cost)
    total_budget = round(sum(resource.monthly_budget for resource in resources), 2)
    budget_pressure = round(projected_30d_cost / total_budget, 3) if total_budget else 0.0
    saving_potential = round(sum(insight.estimated_saving for insight in insight_models), 2)
    risk_level = "低"
    if budget_pressure >= 1 or any(insight.severity == "critical" for insight in insight_models):
        risk_level = "高"
    elif budget_pressure >= 0.75 or anomalies:
        risk_level = "中"

    if persist:
        db.execute(delete(CloudInsight))
        for insight in insight_models:
            db.add(insight)
        add_audit_event(db, "insights_recomputed", "cloud_insight", "重新生成智能优化建议")
        db.commit()
        insight_models = db.scalars(
            select(CloudInsight).order_by(CloudInsight.impact_score.desc(), CloudInsight.created_at.desc())
        ).all()

    return InsightsDashboard(
        generated_at=datetime.now(UTC),
        forecast=forecast,
        projected_30d_cost=projected_30d_cost,
        projected_30d_carbon_kg=projected_30d_carbon,
        total_budget=total_budget,
        budget_pressure=budget_pressure,
        saving_potential=saving_potential,
        risk_level=risk_level,
        recommendations=[InsightRead.model_validate(insight) for insight in insight_models],
        anomalies=anomalies,
    )


def simulate_optimization(payload: SimulationRequest) -> SimulationResponse:
    current_usage = UsageCreate(
        resource_id="simulation",
        record_date=date.today(),
        cpu_core_hours=payload.cpu_core_hours,
        memory_gb_hours=payload.memory_gb_hours,
        storage_gb_hours=payload.storage_gb_hours,
        network_gb=payload.network_gb,
        utilization_score=payload.utilization_score,
    )
    current_daily_cost = compute_estimated_cost(current_usage)
    current_daily_carbon = compute_carbon_kg(current_usage)
    if payload.utilization_score >= payload.target_utilization_score:
        factor = 1.0
    else:
        factor = max(0.55, payload.utilization_score / payload.target_utilization_score)
    optimized_usage = UsageCreate(
        resource_id="simulation",
        record_date=date.today(),
        cpu_core_hours=payload.cpu_core_hours * factor,
        memory_gb_hours=payload.memory_gb_hours * factor,
        storage_gb_hours=payload.storage_gb_hours,
        network_gb=payload.network_gb,
        utilization_score=payload.target_utilization_score,
    )
    optimized_daily_cost = compute_estimated_cost(optimized_usage)
    optimized_daily_carbon = compute_carbon_kg(optimized_usage)
    current_period_cost = round(current_daily_cost * payload.days, 2)
    optimized_period_cost = round(optimized_daily_cost * payload.days, 2)
    saving = round(max(0.0, current_period_cost - optimized_period_cost), 2)
    current_carbon = round(current_daily_carbon * payload.days, 2)
    optimized_carbon = round(optimized_daily_carbon * payload.days, 2)
    carbon_reduction = round(max(0.0, current_carbon - optimized_carbon), 2)
    return SimulationResponse(
        current_period_cost=current_period_cost,
        optimized_period_cost=optimized_period_cost,
        saving=saving,
        saving_ratio=round(saving / current_period_cost, 3) if current_period_cost else 0,
        current_carbon_kg=current_carbon,
        optimized_carbon_kg=optimized_carbon,
        carbon_reduction_kg=carbon_reduction,
        recommendation=(
            f"将平均利用率从 {payload.utilization_score:.0f}% 提升到 {payload.target_utilization_score:.0f}% 后，"
            f"可按比例压缩计算和内存资源，{payload.days} 天预计节省 {saving:.2f} 元。"
        ),
    )


def _alert(
    rule_key: str,
    alert_type: str,
    severity: str,
    title: str,
    description: str,
    metric_value: float,
    threshold_value: float,
    resource: CloudResource | None = None,
    status: str = "open",
) -> CloudAlert:
    return CloudAlert(
        id=uuid_str(),
        rule_key=rule_key,
        alert_type=alert_type,
        severity=severity,
        title=title,
        description=description,
        resource_id=resource.id if resource else None,
        resource_name=resource.name if resource else None,
        metric_value=round(metric_value, 3),
        threshold_value=round(threshold_value, 3),
        status=status,
        created_at=datetime.now(UTC),
    )


def _build_alerts(db: Session) -> list[CloudAlert]:
    resources, records = _recent_records(db)
    records_by_resource: dict[str, list[UsageRecord]] = defaultdict(list)
    for record in records:
        records_by_resource[record.resource_id].append(record)

    forecast, projected_30d_cost, _ = _build_forecast(records)
    anomalies = _detect_anomalies(resources, records)
    alerts: list[CloudAlert] = []

    total_budget = sum(resource.monthly_budget for resource in resources)
    if total_budget > 0:
        pressure = projected_30d_cost / total_budget
        if pressure >= 0.85:
            alerts.append(
                _alert(
                    "forecast:budget-pressure",
                    "forecast",
                    "critical" if pressure >= 1 else "high",
                    "未来 30 天预测成本接近总预算",
                    f"预测成本 {projected_30d_cost:.2f} 元，总预算 {total_budget:.2f} 元，预算压力 {pressure:.0%}。",
                    pressure,
                    0.85,
                )
            )

    for resource in resources:
        resource_records = records_by_resource.get(resource.id, [])
        used_cost = sum(record.estimated_cost for record in resource_records)
        carbon_kg = sum(record.carbon_kg for record in resource_records)
        avg_utilization = (
            sum(record.utilization_score for record in resource_records) / len(resource_records)
            if resource_records
            else 0
        )
        if resource.monthly_budget > 0:
            ratio = used_cost / resource.monthly_budget
            if ratio >= 0.8:
                alerts.append(
                    _alert(
                        f"budget:{resource.id}",
                        "budget",
                        "critical" if ratio >= 1 else "high",
                        f"{resource.name} 预算使用率过高",
                        f"近 30 天成本 {used_cost:.2f} 元，月预算 {resource.monthly_budget:.2f} 元。",
                        ratio,
                        0.8,
                        resource,
                    )
                )
        if used_cost > 40 and avg_utilization < 45:
            alerts.append(
                _alert(
                    f"utilization:{resource.id}",
                    "utilization",
                    "medium",
                    f"{resource.name} 利用率偏低",
                    f"平均利用率 {avg_utilization:.1f}%，但近 30 天成本 {used_cost:.2f} 元，建议降配或合并任务。",
                    avg_utilization,
                    45,
                    resource,
                )
            )
        if carbon_kg > 45:
            alerts.append(
                _alert(
                    f"carbon:{resource.id}",
                    "carbon",
                    "medium",
                    f"{resource.name} 碳排放偏高",
                    f"近 30 天碳排放估算 {carbon_kg:.1f} kg，建议迁移非实时任务到低峰或提升利用率。",
                    carbon_kg,
                    45,
                    resource,
                )
            )

    for anomaly in anomalies:
        resource = next(
            (item for item in resources if item.name == anomaly.resource_name),
            None,
        )
        alerts.append(
            _alert(
                f"anomaly:{anomaly.resource_name}:{anomaly.date.isoformat()}",
                "anomaly",
                "high",
                f"{anomaly.resource_name} 成本尖峰",
                f"{anomaly.date.isoformat()} 成本 {anomaly.actual_cost:.2f} 元，基线 {anomaly.baseline_cost:.2f} 元。",
                anomaly.deviation_ratio,
                0.35,
                resource,
            )
        )

    if forecast and max(item.predicted_cost for item in forecast) == 0 and resources:
        alerts.append(
            _alert(
                "data:no-recent-usage",
                "data_quality",
                "medium",
                "近期缺少用量数据",
                "当前资源存在，但预测窗口内没有可用于趋势分析的用量数据，建议导入账单或采集监控数据。",
                0,
                1,
            )
        )

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda item: (severity_rank.get(item.severity, 9), -item.metric_value))
    return alerts[:20]


def recompute_alerts(db: Session) -> AlertSummary:
    existing_status = {
        alert.rule_key: (alert.status, alert.acknowledged_at)
        for alert in db.scalars(select(CloudAlert)).all()
    }
    db.execute(delete(CloudAlert))
    new_alerts = _build_alerts(db)
    for alert in new_alerts:
        old_status = existing_status.get(alert.rule_key)
        if old_status:
            alert.status = old_status[0]
            alert.acknowledged_at = old_status[1]
        db.add(alert)
    add_audit_event(db, "alerts_recomputed", "cloud_alert", "重新生成云资源告警")
    db.commit()
    return get_alert_summary(db)


def get_alert_summary(db: Session, limit: int = 20) -> AlertSummary:
    alerts = db.scalars(
        select(CloudAlert).order_by(CloudAlert.created_at.desc()).limit(limit)
    ).all()
    all_alerts = db.scalars(select(CloudAlert)).all()
    open_alerts = [alert for alert in all_alerts if alert.status == "open"]
    return AlertSummary(
        total=len(all_alerts),
        open_count=len(open_alerts),
        critical_count=sum(1 for alert in open_alerts if alert.severity == "critical"),
        high_count=sum(1 for alert in open_alerts if alert.severity == "high"),
        alerts=[AlertRead.model_validate(alert) for alert in alerts],
    )


def acknowledge_alert(db: Session, alert_id: str) -> CloudAlert | None:
    alert = db.get(CloudAlert, alert_id)
    if not alert:
        return None
    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.now(UTC)
    add_audit_event(db, "alert_acknowledged", "cloud_alert", f"确认告警 {alert.title}", alert.id)
    db.commit()
    db.refresh(alert)
    return alert


def import_usage_csv(db: Session, content: bytes) -> ImportResult:
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(decoded))
    errors: list[str] = []
    imported_count = 0
    created_resources = 0
    skipped_rows = 0

    if not reader.fieldnames:
        return ImportResult(imported_count=0, created_resources=0, skipped_rows=0, errors=["CSV 文件为空"])

    resources = db.scalars(select(CloudResource)).all()
    resources_by_id = {resource.id: resource for resource in resources}
    resources_by_name = {resource.name: resource for resource in resources}

    for row_number, row in enumerate(reader, start=2):
        try:
            resource = None
            resource_id = (row.get("resource_id") or "").strip()
            resource_name = (row.get("resource_name") or row.get("name") or "").strip()
            if resource_id:
                resource = resources_by_id.get(resource_id)
            if not resource and resource_name:
                resource = resources_by_name.get(resource_name)
            if not resource and resource_name:
                resource = create_resource(
                    db,
                    ResourceCreate(
                        name=resource_name,
                        provider=(row.get("provider") or "Huawei Cloud").strip(),
                        region=(row.get("region") or "cn-east-3").strip(),
                        resource_type=(row.get("resource_type") or "ECS").strip(),
                        owner=(row.get("owner") or "导入数据").strip(),
                        status="active",
                        monthly_budget=float(row.get("monthly_budget") or 500),
                    ),
                )
                resources_by_id[resource.id] = resource
                resources_by_name[resource.name] = resource
                created_resources += 1
            if not resource:
                raise ValueError("缺少 resource_id 或 resource_name，且无法匹配资源")

            payload = UsageCreate(
                resource_id=resource.id,
                record_date=date.fromisoformat((row.get("record_date") or "").strip()),
                cpu_core_hours=float(row.get("cpu_core_hours") or 0),
                memory_gb_hours=float(row.get("memory_gb_hours") or 0),
                storage_gb_hours=float(row.get("storage_gb_hours") or 0),
                network_gb=float(row.get("network_gb") or 0),
                utilization_score=float(row.get("utilization_score") or 0),
                estimated_cost=float(row["estimated_cost"]) if row.get("estimated_cost") else None,
                carbon_kg=float(row["carbon_kg"]) if row.get("carbon_kg") else None,
            )
            create_usage_record(db, payload)
            imported_count += 1
        except Exception as exc:
            skipped_rows += 1
            errors.append(f"第 {row_number} 行导入失败：{exc}")

    add_audit_event(
        db,
        "usage_csv_imported",
        "usage_record",
        f"CSV 导入 {imported_count} 条用量记录，创建 {created_resources} 个资源",
    )
    db.commit()
    return ImportResult(
        imported_count=imported_count,
        created_resources=created_resources,
        skipped_rows=skipped_rows,
        errors=errors[:10],
    )


def generate_ops_report_markdown(db: Session) -> str:
    overview = build_analytics_overview(db)
    insights = build_insights_dashboard(db)
    alert_summary = get_alert_summary(db)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# CloudCostLab 云资源运维周报",
        "",
        f"生成时间：{generated_at}",
        "",
        "## 1. 核心指标",
        "",
        f"- 资源总数：{overview.resource_count}",
        f"- 活跃资源：{overview.active_count}",
        f"- 近 30 天成本：{overview.total_cost:.2f} 元",
        f"- 近 30 天碳排放：{overview.carbon_kg:.2f} kg",
        f"- 平均利用率：{overview.avg_utilization_score:.1f}%",
        f"- 预算风险资源数：{overview.risk_count}",
        f"- 预测 30 天成本：{insights.projected_30d_cost:.2f} 元",
        f"- 预计可节省：{insights.saving_potential:.2f} 元",
        "",
        "## 2. 告警概况",
        "",
        f"- 告警总数：{alert_summary.total}",
        f"- 未确认告警：{alert_summary.open_count}",
        f"- 严重告警：{alert_summary.critical_count}",
        f"- 高危告警：{alert_summary.high_count}",
        "",
        "## 3. 重点告警",
        "",
    ]
    if alert_summary.alerts:
        for alert in alert_summary.alerts[:8]:
            lines.append(
                f"- [{alert.severity}] {alert.title}：{alert.description}（状态：{alert.status}）"
            )
    else:
        lines.append("- 当前无告警。")

    lines.extend(["", "## 4. 优化建议", ""])
    if insights.recommendations:
        for item in insights.recommendations[:8]:
            lines.append(f"- {item.title}：{item.description}预计节省 {item.estimated_saving:.2f} 元。")
    else:
        lines.append("- 当前无优化建议。")

    lines.extend(["", "## 5. 异常成本尖峰", ""])
    if insights.anomalies:
        for anomaly in insights.anomalies[:6]:
            lines.append(
                f"- {anomaly.date.isoformat()} {anomaly.resource_name} 成本 {anomaly.actual_cost:.2f} 元，"
                f"基线 {anomaly.baseline_cost:.2f} 元，偏离 {anomaly.deviation_ratio:.0%}。"
            )
    else:
        lines.append("- 当前未检测到异常成本尖峰。")

    lines.extend(
        [
            "",
            "## 6. 下周行动计划",
            "",
            "- 优先处理 critical/high 告警，确认预算超支和异常成本来源。",
            "- 对低利用率且高成本资源执行降配或自动伸缩策略。",
            "- 对碳排放偏高的批处理任务调整到低峰时段运行。",
            "- 持续导入账单 CSV，保证趋势预测和告警规则有足够数据。",
        ]
    )
    return "\n".join(lines) + "\n"


def seed_demo_data(db: Session, reset: bool = False) -> None:
    if reset:
        db.execute(delete(AuditEvent))
        db.execute(delete(CloudAlert))
        db.execute(delete(CloudInsight))
        db.execute(delete(AnalyticsSnapshot))
        db.execute(delete(UsageRecord))
        db.execute(delete(CloudResource))
        db.commit()

    existing_count = db.scalar(select(func.count(CloudResource.id))) or 0
    if existing_count:
        return

    resources = [
        ResourceCreate(
            name="ecs-billing-api",
            provider="Huawei Cloud",
            region="cn-east-3",
            resource_type="ECS",
            owner="平台组",
            status="active",
            monthly_budget=520,
        ),
        ResourceCreate(
            name="gaussdb-core",
            provider="Huawei Cloud",
            region="cn-north-4",
            resource_type="GaussDB",
            owner="数据组",
            status="active",
            monthly_budget=880,
        ),
        ResourceCreate(
            name="obs-log-archive",
            provider="Huawei Cloud",
            region="cn-south-1",
            resource_type="OBS",
            owner="运维组",
            status="active",
            monthly_budget=240,
        ),
        ResourceCreate(
            name="mrs-spark-etl",
            provider="Huawei Cloud",
            region="cn-east-3",
            resource_type="MRS/Spark",
            owner="数据组",
            status="paused",
            monthly_budget=760,
        ),
    ]

    created = [create_resource(db, payload) for payload in resources]
    today = date.today()
    for day_offset in range(21):
        current_day = today - timedelta(days=20 - day_offset)
        for index, resource in enumerate(created):
            multiplier = 1 + index * 0.35 + (day_offset % 5) * 0.08
            payload = UsageCreate(
                resource_id=resource.id,
                record_date=current_day,
                cpu_core_hours=round(28 * multiplier, 1),
                memory_gb_hours=round(96 * multiplier, 1),
                storage_gb_hours=round(520 * (1 + index * 0.2), 1),
                network_gb=round(18 * multiplier, 1),
                utilization_score=min(98, round(58 + index * 7 + (day_offset % 6) * 3, 1)),
            )
            create_usage_record(db, payload)

    create_usage_record(
        db,
        UsageCreate(
            resource_id=created[3].id,
            record_date=today - timedelta(days=3),
            cpu_core_hours=260,
            memory_gb_hours=820,
            storage_gb_hours=920,
            network_gb=140,
            utilization_score=91,
        ),
    )
    recompute_snapshot(db, generated_by="seed")

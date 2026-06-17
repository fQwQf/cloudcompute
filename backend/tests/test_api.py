import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_SEED"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


client = TestClient(app)


def setup_module() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_resource_usage_and_analytics_flow() -> None:
    resource_response = client.post(
        "/api/resources",
        json={
            "name": "ecs-test",
            "provider": "Huawei Cloud",
            "region": "cn-east-3",
            "resource_type": "ECS",
            "owner": "测试组",
            "status": "active",
            "monthly_budget": 120,
        },
    )
    assert resource_response.status_code == 201
    resource_id = resource_response.json()["id"]

    usage_response = client.post(
        "/api/usage-records",
        json={
            "resource_id": resource_id,
            "record_date": "2026-06-15",
            "cpu_core_hours": 18,
            "memory_gb_hours": 64,
            "storage_gb_hours": 240,
            "network_gb": 9,
            "utilization_score": 72,
        },
    )
    assert usage_response.status_code == 201
    assert usage_response.json()["estimated_cost"] > 0

    overview_response = client.get("/api/analytics/overview?days=30")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["resource_count"] == 1
    assert overview["active_count"] == 1
    assert overview["total_cost"] > 0

    snapshot_response = client.post("/api/analytics/recompute")
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["generated_by"] == "api"

    insights_response = client.get("/api/insights/dashboard")
    assert insights_response.status_code == 200
    insights = insights_response.json()
    assert "forecast" in insights
    assert len(insights["forecast"]) == 7

    simulate_response = client.post(
        "/api/insights/simulate",
        json={
            "cpu_core_hours": 36,
            "memory_gb_hours": 128,
            "storage_gb_hours": 500,
            "network_gb": 20,
            "utilization_score": 35,
            "target_utilization_score": 75,
            "days": 30,
        },
    )
    assert simulate_response.status_code == 200
    assert simulate_response.json()["saving"] > 0


def test_seed_and_export() -> None:
    seed_response = client.post("/api/demo/seed", json={"reset": True})
    assert seed_response.status_code == 200

    resources_response = client.get("/api/resources")
    assert resources_response.status_code == 200
    assert len(resources_response.json()) >= 4

    export_response = client.get("/api/export/resources.csv")
    assert export_response.status_code == 200
    assert "cloud-resources.csv" in export_response.headers["content-disposition"]

    recompute_response = client.post("/api/insights/recompute")
    assert recompute_response.status_code == 200
    assert recompute_response.json()["risk_level"] in {"低", "中", "高"}

    alerts_response = client.post("/api/operations/alerts/recompute")
    assert alerts_response.status_code == 200
    alerts = alerts_response.json()
    assert alerts["total"] >= 1

    ack_response = client.post(f"/api/operations/alerts/{alerts['alerts'][0]['id']}/ack")
    assert ack_response.status_code == 200
    assert ack_response.json()["status"] == "acknowledged"

    report_response = client.get("/api/operations/reports/weekly.md")
    assert report_response.status_code == 200
    assert "CloudCostLab 云资源运维周报" in report_response.text


def test_usage_csv_import_creates_resource_and_records() -> None:
    csv_content = (
        "resource_name,provider,region,resource_type,owner,monthly_budget,record_date,"
        "cpu_core_hours,memory_gb_hours,storage_gb_hours,network_gb,utilization_score\n"
        "csv-import-ecs,Huawei Cloud,cn-east-3,ECS,导入组,260,2026-06-15,10,30,120,4,55\n"
    )
    response = client.post(
        "/api/operations/import/usage-csv",
        files={"file": ("usage.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["imported_count"] == 1
    assert result["created_resources"] == 1

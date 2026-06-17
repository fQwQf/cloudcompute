CREATE TABLE IF NOT EXISTS cloud_resources (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    provider VARCHAR(40) NOT NULL DEFAULT 'Huawei Cloud',
    region VARCHAR(80) NOT NULL,
    resource_type VARCHAR(40) NOT NULL,
    owner VARCHAR(80) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    monthly_budget DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_records (
    id VARCHAR(36) PRIMARY KEY,
    resource_id VARCHAR(36) NOT NULL REFERENCES cloud_resources(id),
    record_date DATE NOT NULL,
    cpu_core_hours DOUBLE PRECISION NOT NULL DEFAULT 0,
    memory_gb_hours DOUBLE PRECISION NOT NULL DEFAULT 0,
    storage_gb_hours DOUBLE PRECISION NOT NULL DEFAULT 0,
    network_gb DOUBLE PRECISION NOT NULL DEFAULT 0,
    estimated_cost DOUBLE PRECISION NOT NULL DEFAULT 0,
    carbon_kg DOUBLE PRECISION NOT NULL DEFAULT 0,
    utilization_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id VARCHAR(36) PRIMARY KEY,
    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resource_count INTEGER NOT NULL DEFAULT 0,
    active_count INTEGER NOT NULL DEFAULT 0,
    total_cost DOUBLE PRECISION NOT NULL DEFAULT 0,
    avg_utilization_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    carbon_kg DOUBLE PRECISION NOT NULL DEFAULT 0,
    top_region VARCHAR(80) NOT NULL DEFAULT '-',
    risk_count INTEGER NOT NULL DEFAULT 0,
    generated_by VARCHAR(40) NOT NULL DEFAULT 'api'
);

CREATE TABLE IF NOT EXISTS cloud_insights (
    id VARCHAR(36) PRIMARY KEY,
    category VARCHAR(40) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    resource_id VARCHAR(36),
    resource_name VARCHAR(120),
    impact_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    estimated_saving DOUBLE PRECISION NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cloud_alerts (
    id VARCHAR(36) PRIMARY KEY,
    rule_key VARCHAR(160) NOT NULL,
    alert_type VARCHAR(40) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    resource_id VARCHAR(36),
    resource_name VARCHAR(120),
    metric_value DOUBLE PRECISION NOT NULL DEFAULT 0,
    threshold_value DOUBLE PRECISION NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
    id VARCHAR(36) PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

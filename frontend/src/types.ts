export type Resource = {
  id: string;
  name: string;
  provider: string;
  region: string;
  resource_type: string;
  owner: string;
  status: 'active' | 'paused' | 'retired';
  monthly_budget: number;
  created_at: string;
  updated_at: string;
};

export type UsageRecord = {
  id: string;
  resource_id: string;
  resource_name?: string;
  record_date: string;
  cpu_core_hours: number;
  memory_gb_hours: number;
  storage_gb_hours: number;
  network_gb: number;
  estimated_cost: number;
  carbon_kg: number;
  utilization_score: number;
  created_at: string;
};

export type AuditEvent = {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id?: string;
  message: string;
  created_at: string;
};

export type Overview = {
  resource_count: number;
  active_count: number;
  total_cost: number;
  avg_utilization_score: number;
  carbon_kg: number;
  top_region: string;
  risk_count: number;
  trend: Array<{ date: string; cost: number; carbon_kg: number; avg_utilization_score: number }>;
  cost_by_resource: Array<{ label: string; value: number }>;
  cost_by_region: Array<{ label: string; value: number }>;
  budget_risks: Array<{
    resource_id: string;
    name: string;
    owner: string;
    used_cost: number;
    monthly_budget: number;
    budget_ratio: number;
  }>;
  latest_snapshot?: {
    snapshot_time: string;
    generated_by: string;
  };
};

export type Insight = {
  id: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  resource_id?: string;
  resource_name?: string;
  impact_score: number;
  estimated_saving: number;
  status: string;
  created_at: string;
};

export type InsightsDashboard = {
  generated_at: string;
  forecast: Array<{ date: string; predicted_cost: number; predicted_carbon_kg: number }>;
  projected_30d_cost: number;
  projected_30d_carbon_kg: number;
  total_budget: number;
  budget_pressure: number;
  saving_potential: number;
  risk_level: string;
  recommendations: Insight[];
  anomalies: Array<{
    date: string;
    resource_name: string;
    actual_cost: number;
    baseline_cost: number;
    deviation_ratio: number;
    reason: string;
  }>;
};

export type ResourceForm = {
  name: string;
  provider: string;
  region: string;
  resource_type: string;
  owner: string;
  status: 'active' | 'paused' | 'retired';
  monthly_budget: string;
};

export type UsageForm = {
  resource_id: string;
  record_date: string;
  cpu_core_hours: string;
  memory_gb_hours: string;
  storage_gb_hours: string;
  network_gb: string;
  utilization_score: string;
};

export type SimulationForm = {
  cpu_core_hours: string;
  memory_gb_hours: string;
  storage_gb_hours: string;
  network_gb: string;
  utilization_score: string;
  target_utilization_score: string;
  days: string;
};

export type SimulationResult = {
  current_period_cost: number;
  optimized_period_cost: number;
  saving: number;
  saving_ratio: number;
  current_carbon_kg: number;
  optimized_carbon_kg: number;
  carbon_reduction_kg: number;
  recommendation: string;
};

export type CloudAlert = {
  id: string;
  rule_key: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  resource_id?: string;
  resource_name?: string;
  metric_value: number;
  threshold_value: number;
  status: 'open' | 'acknowledged';
  created_at: string;
  acknowledged_at?: string;
};

export type AlertSummary = {
  total: number;
  open_count: number;
  critical_count: number;
  high_count: number;
  alerts: CloudAlert[];
};

export type ImportResult = {
  imported_count: number;
  created_resources: number;
  skipped_rows: number;
  errors: string[];
};

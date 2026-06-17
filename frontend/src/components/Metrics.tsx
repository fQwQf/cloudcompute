import { Activity, Bell, BrainCircuit, Database, Leaf, Server, ShieldAlert } from 'lucide-react';

import { money } from '../format';
import type { AlertSummary, InsightsDashboard, Overview } from '../types';

type MetricsProps = {
  overview: Overview | null;
  insights: InsightsDashboard | null;
  alertSummary: AlertSummary | null;
};

export function Metrics({ overview, insights, alertSummary }: MetricsProps) {
  const metrics = [
    {
      label: '资源总数',
      value: overview?.resource_count ?? 0,
      icon: Server,
      tone: 'teal'
    },
    {
      label: '活跃资源',
      value: overview?.active_count ?? 0,
      icon: Activity,
      tone: 'green'
    },
    {
      label: '近 30 天成本',
      value: money(overview?.total_cost ?? 0),
      icon: Database,
      tone: 'amber'
    },
    {
      label: '碳排放 kg',
      value: (overview?.carbon_kg ?? 0).toFixed(1),
      icon: Leaf,
      tone: 'lime'
    },
    {
      label: '预算风险',
      value: overview?.risk_count ?? 0,
      icon: ShieldAlert,
      tone: 'rose'
    },
    {
      label: '节省潜力',
      value: money(insights?.saving_potential ?? 0),
      icon: BrainCircuit,
      tone: 'teal'
    },
    {
      label: '未确认告警',
      value: alertSummary?.open_count ?? 0,
      icon: Bell,
      tone: 'rose'
    }
  ];

  return (
    <section className="metric-grid" id="dashboard">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <article className={`metric-card ${metric.tone}`} key={metric.label}>
            <Icon size={20} />
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </article>
        );
      })}
    </section>
  );
}

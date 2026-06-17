import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import type { Overview } from '../types';

type OverviewChartsProps = {
  overview: Overview | null;
};

export function OverviewCharts({ overview }: OverviewChartsProps) {
  return (
    <section className="analytics-layout">
      <div className="panel wide">
        <div className="panel-head">
          <h2>近 30 天趋势</h2>
          <span>Top Region: {overview?.top_region ?? '-'}</span>
        </div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={overview?.trend ?? []}>
              <defs>
                <linearGradient id="costFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#0f8b8d" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#0f8b8d" stopOpacity={0.04} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#d9e1e8" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="cost"
                name="成本"
                stroke="#0f8b8d"
                strokeWidth={2}
                fill="url(#costFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>资源成本</h2>
        </div>
        <div className="chart-frame compact">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={overview?.cost_by_resource ?? []} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#d9e1e8" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="label" type="category" width={112} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" name="成本" fill="#e28413" radius={[0, 5, 5, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}

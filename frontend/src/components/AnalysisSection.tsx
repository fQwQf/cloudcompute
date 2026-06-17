import type { Dispatch, FormEvent, SetStateAction } from 'react';
import { AlertTriangle, Calculator, Gauge, Leaf, Target, TrendingUp } from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

import { money, percent, shortTime } from '../format';
import type { InsightsDashboard, SimulationForm, SimulationResult } from '../types';

type AnalysisSectionProps = {
  insights: InsightsDashboard | null;
  simulationForm: SimulationForm;
  simulationResult: SimulationResult | null;
  busy: boolean;
  setSimulationForm: Dispatch<SetStateAction<SimulationForm>>;
  onSimulate: (event: FormEvent) => void;
};

export function AnalysisSection({
  insights,
  simulationForm,
  simulationResult,
  busy,
  setSimulationForm,
  onSimulate
}: AnalysisSectionProps) {
  return (
    <>
      <section className="insight-grid" id="insights">
        <div className="panel insight-hero">
          <div className="panel-head">
            <div>
              <h2>成本分析</h2>
              <span>预测、异常和优化建议</span>
            </div>
            <strong className={`risk-level risk-${insights?.risk_level ?? '低'}`}>
              风险 {insights?.risk_level ?? '-'}
            </strong>
          </div>
          <div className="insight-stats">
            <div>
              <TrendingUp size={18} />
              <span>预测 30 天成本</span>
              <strong>{money(insights?.projected_30d_cost ?? 0)}</strong>
            </div>
            <div>
              <Leaf size={18} />
              <span>预测碳排放</span>
              <strong>{(insights?.projected_30d_carbon_kg ?? 0).toFixed(1)} kg</strong>
            </div>
            <div>
              <Gauge size={18} />
              <span>预算压力</span>
              <strong>{percent(insights?.budget_pressure ?? 0)}</strong>
            </div>
            <div>
              <Target size={18} />
              <span>可节省</span>
              <strong>{money(insights?.saving_potential ?? 0)}</strong>
            </div>
          </div>
          <div className="chart-frame compact">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={insights?.forecast ?? []}>
                <defs>
                  <linearGradient id="forecastFill" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#3f9d69" stopOpacity={0.32} />
                    <stop offset="100%" stopColor="#3f9d69" stopOpacity={0.04} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#d9e1e8" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="predicted_cost"
                  name="预测成本"
                  stroke="#3f9d69"
                  strokeWidth={2}
                  fill="url(#forecastFill)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel simulator-panel">
          <div className="panel-head">
            <h2>优化模拟</h2>
            <Calculator size={19} />
          </div>
          <form className="form-grid" onSubmit={onSimulate}>
            <label>
              CPU 核时
              <input
                type="number"
                min="0"
                value={simulationForm.cpu_core_hours}
                onChange={(event) =>
                  setSimulationForm({ ...simulationForm, cpu_core_hours: event.target.value })
                }
              />
            </label>
            <label>
              内存 GB时
              <input
                type="number"
                min="0"
                value={simulationForm.memory_gb_hours}
                onChange={(event) =>
                  setSimulationForm({ ...simulationForm, memory_gb_hours: event.target.value })
                }
              />
            </label>
            <label>
              存储 GB时
              <input
                type="number"
                min="0"
                value={simulationForm.storage_gb_hours}
                onChange={(event) =>
                  setSimulationForm({ ...simulationForm, storage_gb_hours: event.target.value })
                }
              />
            </label>
            <label>
              网络 GB
              <input
                type="number"
                min="0"
                value={simulationForm.network_gb}
                onChange={(event) =>
                  setSimulationForm({ ...simulationForm, network_gb: event.target.value })
                }
              />
            </label>
            <label>
              当前利用率
              <input
                type="number"
                min="1"
                max="100"
                value={simulationForm.utilization_score}
                onChange={(event) =>
                  setSimulationForm({ ...simulationForm, utilization_score: event.target.value })
                }
              />
            </label>
            <label>
              目标利用率
              <input
                type="number"
                min="1"
                max="100"
                value={simulationForm.target_utilization_score}
                onChange={(event) =>
                  setSimulationForm({
                    ...simulationForm,
                    target_utilization_score: event.target.value
                  })
                }
              />
            </label>
            <label>
              周期天数
              <input
                type="number"
                min="1"
                max="365"
                value={simulationForm.days}
                onChange={(event) => setSimulationForm({ ...simulationForm, days: event.target.value })}
              />
            </label>
            <button className="primary form-submit" disabled={busy}>
              <Calculator size={17} />
              开始模拟
            </button>
          </form>
          {simulationResult && (
            <div className="simulation-result">
              <div>
                <span>优化前</span>
                <strong>{money(simulationResult.current_period_cost)}</strong>
              </div>
              <div>
                <span>优化后</span>
                <strong>{money(simulationResult.optimized_period_cost)}</strong>
              </div>
              <div>
                <span>节省</span>
                <strong>{money(simulationResult.saving)}</strong>
              </div>
              <p>{simulationResult.recommendation}</p>
            </div>
          )}
        </div>
      </section>

      <section className="insight-lists">
        <div className="panel">
          <div className="panel-head">
            <h2>优化建议</h2>
            <span>{shortTime(insights?.generated_at)}</span>
          </div>
          <div className="recommendation-list">
            {(insights?.recommendations ?? []).map((item) => (
              <div className={`recommendation-row severity-${item.severity}`} key={item.id}>
                <div className="recommendation-title">
                  <strong>{item.title}</strong>
                  <span>{item.category}</span>
                </div>
                <p>{item.description}</p>
                <div className="recommendation-meta">
                  <span>影响 {item.impact_score.toFixed(0)}</span>
                  <span>预计节省 {money(item.estimated_saving)}</span>
                  {item.resource_name && <span>{item.resource_name}</span>}
                </div>
              </div>
            ))}
            {!insights?.recommendations.length && <p className="empty">暂无优化建议</p>}
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h2>异常成本尖峰</h2>
            <AlertTriangle size={19} />
          </div>
          <div className="anomaly-list">
            {(insights?.anomalies ?? []).map((item) => (
              <div className="anomaly-row" key={`${item.resource_name}-${item.date}`}>
                <div>
                  <strong>{item.resource_name}</strong>
                  <span>{item.date}</span>
                </div>
                <div>
                  <strong>{money(item.actual_cost)}</strong>
                  <span>基线 {money(item.baseline_cost)}</span>
                </div>
                <em>+{percent(item.deviation_ratio)}</em>
              </div>
            ))}
            {!insights?.anomalies.length && <p className="empty">暂无异常尖峰</p>}
          </div>
        </div>
      </section>
    </>
  );
}

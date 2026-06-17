import { money, percent, shortTime } from '../format';
import type { AuditEvent, Overview, UsageRecord } from '../types';

type ActivityPanelsProps = {
  overview: Overview | null;
  usageRecords: UsageRecord[];
  auditLog: AuditEvent[];
};

export function ActivityPanels({ overview, usageRecords, auditLog }: ActivityPanelsProps) {
  return (
    <section className="bottom-grid" id="audit">
      <div className="panel">
        <div className="panel-head">
          <h2>预算风险</h2>
        </div>
        <div className="risk-list">
          {(overview?.budget_risks ?? []).map((risk) => (
            <div className="risk-row" key={risk.resource_id}>
              <div>
                <strong>{risk.name}</strong>
                <span>{risk.owner}</span>
              </div>
              <div className="risk-meter">
                <span style={{ width: `${Math.min(risk.budget_ratio * 100, 100)}%` }} />
              </div>
              <em>{percent(risk.budget_ratio)}</em>
            </div>
          ))}
          {!overview?.budget_risks.length && <p className="empty">暂无预算风险</p>}
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>最近用量</h2>
        </div>
        <div className="event-list">
          {usageRecords.map((record) => (
            <div className="event-row" key={record.id}>
              <strong>{record.resource_name ?? record.resource_id}</strong>
              <span>
                {record.record_date} · {money(record.estimated_cost)} · {record.utilization_score}%
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>审计日志</h2>
        </div>
        <div className="event-list">
          {auditLog.map((event) => (
            <div className="event-row" key={event.id}>
              <strong>{event.event_type}</strong>
              <span>
                {shortTime(event.created_at)} · {event.message}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

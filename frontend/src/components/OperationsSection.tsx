import type { ChangeEvent } from 'react';
import { Bell, CheckCircle2, FileSpreadsheet, FileText } from 'lucide-react';

import { apiBase } from '../api';
import { shortTime } from '../format';
import type { AlertSummary, ImportResult } from '../types';

type OperationsSectionProps = {
  alertSummary: AlertSummary | null;
  importResult: ImportResult | null;
  busy: boolean;
  onAlertRecompute: () => void;
  onAckAlert: (alertId: string) => void;
  onCsvImport: (event: ChangeEvent<HTMLInputElement>) => void;
};

export function OperationsSection({
  alertSummary,
  importResult,
  busy,
  onAlertRecompute,
  onAckAlert,
  onCsvImport
}: OperationsSectionProps) {
  return (
    <section className="operations-grid" id="operations">
      <div className="panel">
        <div className="panel-head">
          <div>
            <h2>告警处理</h2>
            <span>
              未确认 {alertSummary?.open_count ?? 0} · 严重 {alertSummary?.critical_count ?? 0} · 高危{' '}
              {alertSummary?.high_count ?? 0}
            </span>
          </div>
          <button className="ghost" onClick={onAlertRecompute} disabled={busy}>
            <Bell size={17} />
            执行规则
          </button>
        </div>
        <div className="alert-list">
          {(alertSummary?.alerts ?? []).map((alert) => (
            <div className={`alert-row severity-${alert.severity}`} key={alert.id}>
              <div>
                <div className="alert-title">
                  <strong>{alert.title}</strong>
                  <span>{alert.alert_type}</span>
                </div>
                <p>{alert.description}</p>
                <em>
                  {shortTime(alert.created_at)} · {alert.status}
                </em>
              </div>
              {alert.status === 'open' ? (
                <button className="icon-button" onClick={() => onAckAlert(alert.id)} title="确认告警">
                  <CheckCircle2 size={17} />
                </button>
              ) : (
                <span className="ack-badge">已确认</span>
              )}
            </div>
          ))}
          {!alertSummary?.alerts.length && <p className="empty">点击“执行规则”生成告警</p>}
        </div>
      </div>

      <div className="panel practical-panel">
        <div className="panel-head">
          <h2>导入与周报</h2>
          <FileSpreadsheet size={19} />
        </div>
        <label className="upload-box">
          <FileSpreadsheet size={22} />
          <span>导入账单/用量 CSV</span>
          <input type="file" accept=".csv,text/csv" onChange={onCsvImport} disabled={busy} />
        </label>
        {importResult && (
          <div className="import-result">
            <div>
              <span>导入记录</span>
              <strong>{importResult.imported_count}</strong>
            </div>
            <div>
              <span>新建资源</span>
              <strong>{importResult.created_resources}</strong>
            </div>
            <div>
              <span>跳过行</span>
              <strong>{importResult.skipped_rows}</strong>
            </div>
          </div>
        )}
        {importResult?.errors.length ? (
          <div className="import-errors">
            {importResult.errors.map((error) => (
              <span key={error}>{error}</span>
            ))}
          </div>
        ) : null}
        <a className="primary report-link" href={`${apiBase}/operations/reports/weekly.md`}>
          <FileText size={17} />
          下载运维周报 Markdown
        </a>
      </div>
    </section>
  );
}

import {
  BarChart3,
  Bell,
  BrainCircuit,
  Cloud,
  Download,
  FileText,
  RefreshCcw,
  Sparkles
} from 'lucide-react';

import { apiBase } from '../api';
import { shortTime } from '../format';
import type { Overview } from '../types';

type AppShellProps = {
  overview: Overview | null;
  busy: boolean;
  notice: string;
  children: React.ReactNode;
  onRefresh: () => void;
  onRecompute: () => void;
  onAnalyze: () => void;
  onAlertRecompute: () => void;
  onSeed: () => void;
};

export function AppShell({
  overview,
  busy,
  notice,
  children,
  onRefresh,
  onRecompute,
  onAnalyze,
  onAlertRecompute,
  onSeed
}: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Cloud size={22} />
          </div>
          <div>
            <strong>CloudCostLab</strong>
            <span>openGauss 课程实验</span>
          </div>
        </div>
        <nav>
          <a href="#dashboard">总览</a>
          <a href="#insights">分析</a>
          <a href="#operations">运维</a>
          <a href="#resources">资源</a>
          <a href="#usage">用量</a>
          <a href="#audit">审计</a>
        </nav>
        <div className="sidebar-note">
          <Sparkles size={18} />
          <span>
            {overview?.latest_snapshot
              ? `快照 ${shortTime(overview.latest_snapshot.snapshot_time)}`
              : '暂无快照'}
          </span>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <p className="eyebrow">Huawei Cloud 部署演示</p>
            <h1>云资源成本与碳排放分析平台</h1>
          </div>
          <div className="actions">
            <button className="ghost" onClick={onRefresh} disabled={busy} title="刷新">
              <RefreshCcw size={17} />
              刷新
            </button>
            <button className="ghost" onClick={onRecompute} disabled={busy} title="重新生成分析快照">
              <BarChart3 size={17} />
              聚合
            </button>
            <button className="ghost" onClick={onAnalyze} disabled={busy} title="生成成本分析">
              <BrainCircuit size={17} />
              分析
            </button>
            <button className="ghost" onClick={onAlertRecompute} disabled={busy} title="执行告警规则">
              <Bell size={17} />
              告警
            </button>
            <button className="ghost" onClick={onSeed} disabled={busy} title="重置演示数据">
              <Sparkles size={17} />
              演示数据
            </button>
            <a className="ghost link-button" href={`${apiBase}/operations/reports/weekly.md`} title="下载运维周报">
              <FileText size={17} />
              周报
            </a>
            <a className="primary" href={`${apiBase}/export/resources.csv`} title="导出 CSV">
              <Download size={17} />
              导出
            </a>
          </div>
        </header>

        <div className="status-line">
          <span className={busy ? 'pulse' : ''} />
          {notice}
        </div>

        {children}
      </main>
    </div>
  );
}

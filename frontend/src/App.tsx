import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from 'react';

import { requestJson } from './api';
import { ActivityPanels } from './components/ActivityPanels';
import { AnalysisSection } from './components/AnalysisSection';
import { AppShell } from './components/AppShell';
import { Metrics } from './components/Metrics';
import { OperationsSection } from './components/OperationsSection';
import { OverviewCharts } from './components/OverviewCharts';
import { ResourceForms } from './components/ResourceForms';
import { ResourceTable } from './components/ResourceTable';
import { defaultSimulationForm, emptyResourceForm, emptyUsageForm } from './defaults';
import type {
  AlertSummary,
  AuditEvent,
  CloudAlert,
  ImportResult,
  InsightsDashboard,
  Overview,
  Resource,
  ResourceForm,
  SimulationForm,
  SimulationResult,
  UsageForm,
  UsageRecord
} from './types';

export default function App() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [usageRecords, setUsageRecords] = useState<UsageRecord[]>([]);
  const [auditLog, setAuditLog] = useState<AuditEvent[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [insights, setInsights] = useState<InsightsDashboard | null>(null);
  const [alertSummary, setAlertSummary] = useState<AlertSummary | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [resourceForm, setResourceForm] = useState<ResourceForm>(emptyResourceForm);
  const [usageForm, setUsageForm] = useState<UsageForm>(emptyUsageForm);
  const [simulationForm, setSimulationForm] = useState<SimulationForm>(defaultSimulationForm);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [notice, setNotice] = useState('连接后端中');
  const [busy, setBusy] = useState(false);

  const activeResources = useMemo(
    () => resources.filter((resource) => resource.status !== 'retired'),
    [resources]
  );

  async function loadResources(selectedResourceId = usageForm.resource_id) {
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    if (statusFilter) params.set('status', statusFilter);

    const data = await requestJson<Resource[]>(`/resources?${params.toString()}`);
    setResources(data);
    if (!selectedResourceId && data[0]) {
      setUsageForm((current) => ({ ...current, resource_id: data[0].id }));
    }
  }

  async function loadAll(message = '数据已刷新') {
    setBusy(true);
    try {
      const [overviewData, usageData, auditData, insightsData, alertData] = await Promise.all([
        requestJson<Overview>('/analytics/overview?days=30'),
        requestJson<UsageRecord[]>('/usage-records?limit=8'),
        requestJson<AuditEvent[]>('/audit-log?limit=8'),
        requestJson<InsightsDashboard>('/insights/dashboard'),
        requestJson<AlertSummary>('/operations/alerts')
      ]);
      await loadResources();
      setOverview(overviewData);
      setUsageRecords(usageData);
      setAuditLog(auditData);
      setInsights(insightsData);
      setAlertSummary(alertData);
      setNotice(message);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '请求失败');
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void loadAll('演示数据已载入');
  }, []);

  async function handleSearch(event: FormEvent) {
    event.preventDefault();
    await loadAll('筛选结果已更新');
  }

  async function handleCreateResource(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await requestJson<Resource>('/resources', {
        method: 'POST',
        body: JSON.stringify({
          ...resourceForm,
          monthly_budget: Number(resourceForm.monthly_budget)
        })
      });
      setResourceForm(emptyResourceForm);
      await loadAll('资源已写入 openGauss');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '资源创建失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateUsage(event: FormEvent) {
    event.preventDefault();
    if (!usageForm.resource_id) {
      setNotice('请先选择资源');
      return;
    }

    setBusy(true);
    try {
      await requestJson<UsageRecord>('/usage-records', {
        method: 'POST',
        body: JSON.stringify({
          resource_id: usageForm.resource_id,
          record_date: usageForm.record_date,
          cpu_core_hours: Number(usageForm.cpu_core_hours),
          memory_gb_hours: Number(usageForm.memory_gb_hours),
          storage_gb_hours: Number(usageForm.storage_gb_hours),
          network_gb: Number(usageForm.network_gb),
          utilization_score: Number(usageForm.utilization_score)
        })
      });
      await loadAll('用量记录已写入 openGauss');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '用量写入失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleToggleStatus(resource: Resource) {
    const nextStatus = resource.status === 'active' ? 'paused' : 'active';
    setBusy(true);
    try {
      await requestJson<Resource>(`/resources/${resource.id}`, {
        method: 'PUT',
        body: JSON.stringify({ status: nextStatus })
      });
      await loadAll(`${resource.name} 已切换为 ${nextStatus}`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '状态更新失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(resource: Resource) {
    setBusy(true);
    try {
      await requestJson<void>(`/resources/${resource.id}`, { method: 'DELETE' });
      await loadAll(`${resource.name} 已删除`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '删除失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleSeed(reset: boolean) {
    setBusy(true);
    try {
      await requestJson<{ message: string }>('/demo/seed', {
        method: 'POST',
        body: JSON.stringify({ reset })
      });
      await loadAll(reset ? '演示数据已重置' : '演示数据已检查');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '演示数据生成失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleRecompute() {
    setBusy(true);
    try {
      await requestJson('/analytics/recompute', { method: 'POST' });
      await loadAll('分析快照已写入 openGauss');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '分析快照生成失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleAnalysisRecompute() {
    setBusy(true);
    try {
      const insightsData = await requestJson<InsightsDashboard>('/insights/recompute', { method: 'POST' });
      setInsights(insightsData);
      await loadAll('成本分析已写入 openGauss');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '成本分析生成失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleAlertRecompute() {
    setBusy(true);
    try {
      const alerts = await requestJson<AlertSummary>('/operations/alerts/recompute', { method: 'POST' });
      setAlertSummary(alerts);
      await loadAll('告警规则已执行并写入 openGauss');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '告警生成失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleAckAlert(alertId: string) {
    setBusy(true);
    try {
      await requestJson<CloudAlert>(`/operations/alerts/${alertId}/ack`, { method: 'POST' });
      await loadAll('告警已确认');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '告警确认失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleCsvImport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    setBusy(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const result = await requestJson<ImportResult>('/operations/import/usage-csv', {
        method: 'POST',
        body: formData
      });
      setImportResult(result);
      event.target.value = '';
      await loadAll(`CSV 导入完成：${result.imported_count} 条用量`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'CSV 导入失败');
    } finally {
      setBusy(false);
    }
  }

  async function handleSimulate(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const result = await requestJson<SimulationResult>('/insights/simulate', {
        method: 'POST',
        body: JSON.stringify({
          cpu_core_hours: Number(simulationForm.cpu_core_hours),
          memory_gb_hours: Number(simulationForm.memory_gb_hours),
          storage_gb_hours: Number(simulationForm.storage_gb_hours),
          network_gb: Number(simulationForm.network_gb),
          utilization_score: Number(simulationForm.utilization_score),
          target_utilization_score: Number(simulationForm.target_utilization_score),
          days: Number(simulationForm.days)
        })
      });
      setSimulationResult(result);
      setNotice('优化模拟完成');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : '模拟失败');
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell
      overview={overview}
      busy={busy}
      notice={notice}
      onRefresh={() => loadAll()}
      onRecompute={handleRecompute}
      onAnalyze={handleAnalysisRecompute}
      onAlertRecompute={handleAlertRecompute}
      onSeed={() => handleSeed(true)}
    >
      <Metrics overview={overview} insights={insights} alertSummary={alertSummary} />
      <OverviewCharts overview={overview} />
      <AnalysisSection
        insights={insights}
        simulationForm={simulationForm}
        simulationResult={simulationResult}
        busy={busy}
        setSimulationForm={setSimulationForm}
        onSimulate={handleSimulate}
      />
      <OperationsSection
        alertSummary={alertSummary}
        importResult={importResult}
        busy={busy}
        onAlertRecompute={handleAlertRecompute}
        onAckAlert={handleAckAlert}
        onCsvImport={handleCsvImport}
      />
      <ResourceForms
        resourceForm={resourceForm}
        usageForm={usageForm}
        activeResources={activeResources}
        busy={busy}
        setResourceForm={setResourceForm}
        setUsageForm={setUsageForm}
        onCreateResource={handleCreateResource}
        onCreateUsage={handleCreateUsage}
      />
      <ResourceTable
        resources={resources}
        query={query}
        statusFilter={statusFilter}
        busy={busy}
        setQuery={setQuery}
        setStatusFilter={setStatusFilter}
        onSearch={handleSearch}
        onToggleStatus={handleToggleStatus}
        onDelete={handleDelete}
      />
      <ActivityPanels overview={overview} usageRecords={usageRecords} auditLog={auditLog} />
    </AppShell>
  );
}

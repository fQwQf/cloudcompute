import type { ResourceForm, SimulationForm, UsageForm } from './types';

const today = new Date().toISOString().slice(0, 10);

export const emptyResourceForm: ResourceForm = {
  name: '',
  provider: 'Huawei Cloud',
  region: 'cn-east-3',
  resource_type: 'ECS',
  owner: '',
  status: 'active',
  monthly_budget: '500'
};

export const emptyUsageForm: UsageForm = {
  resource_id: '',
  record_date: today,
  cpu_core_hours: '24',
  memory_gb_hours: '96',
  storage_gb_hours: '500',
  network_gb: '20',
  utilization_score: '70'
};

export const defaultSimulationForm: SimulationForm = {
  cpu_core_hours: '48',
  memory_gb_hours: '192',
  storage_gb_hours: '800',
  network_gb: '32',
  utilization_score: '35',
  target_utilization_score: '75',
  days: '30'
};

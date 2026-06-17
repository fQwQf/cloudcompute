import type { Dispatch, FormEvent, SetStateAction } from 'react';
import { Database, Plus } from 'lucide-react';

import type { Resource, ResourceForm, UsageForm } from '../types';

type ResourceFormsProps = {
  resourceForm: ResourceForm;
  usageForm: UsageForm;
  activeResources: Resource[];
  busy: boolean;
  setResourceForm: Dispatch<SetStateAction<ResourceForm>>;
  setUsageForm: Dispatch<SetStateAction<UsageForm>>;
  onCreateResource: (event: FormEvent) => void;
  onCreateUsage: (event: FormEvent) => void;
};

export function ResourceForms({
  resourceForm,
  usageForm,
  activeResources,
  busy,
  setResourceForm,
  setUsageForm,
  onCreateResource,
  onCreateUsage
}: ResourceFormsProps) {
  return (
    <section className="work-grid">
      <div className="panel" id="resources">
        <div className="panel-head">
          <h2>新增资源</h2>
        </div>
        <form className="form-grid" onSubmit={onCreateResource}>
          <label>
            名称
            <input
              required
              value={resourceForm.name}
              onChange={(event) => setResourceForm({ ...resourceForm, name: event.target.value })}
              placeholder="ecs-prod-api"
            />
          </label>
          <label>
            区域
            <select
              value={resourceForm.region}
              onChange={(event) => setResourceForm({ ...resourceForm, region: event.target.value })}
            >
              <option value="cn-east-3">cn-east-3</option>
              <option value="cn-north-4">cn-north-4</option>
              <option value="cn-south-1">cn-south-1</option>
            </select>
          </label>
          <label>
            类型
            <select
              value={resourceForm.resource_type}
              onChange={(event) =>
                setResourceForm({ ...resourceForm, resource_type: event.target.value })
              }
            >
              <option value="ECS">ECS</option>
              <option value="GaussDB">GaussDB</option>
              <option value="OBS">OBS</option>
              <option value="MRS/Spark">MRS/Spark</option>
            </select>
          </label>
          <label>
            负责人
            <input
              required
              value={resourceForm.owner}
              onChange={(event) => setResourceForm({ ...resourceForm, owner: event.target.value })}
              placeholder="平台组"
            />
          </label>
          <label>
            月预算
            <input
              required
              min="0"
              type="number"
              value={resourceForm.monthly_budget}
              onChange={(event) =>
                setResourceForm({ ...resourceForm, monthly_budget: event.target.value })
              }
            />
          </label>
          <button className="primary form-submit" disabled={busy}>
            <Plus size={17} />
            写入资源
          </button>
        </form>
      </div>

      <div className="panel" id="usage">
        <div className="panel-head">
          <h2>写入用量</h2>
        </div>
        <form className="form-grid" onSubmit={onCreateUsage}>
          <label className="span-two">
            资源
            <select
              value={usageForm.resource_id}
              onChange={(event) => setUsageForm({ ...usageForm, resource_id: event.target.value })}
            >
              {activeResources.map((resource) => (
                <option value={resource.id} key={resource.id}>
                  {resource.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            日期
            <input
              type="date"
              value={usageForm.record_date}
              onChange={(event) => setUsageForm({ ...usageForm, record_date: event.target.value })}
            />
          </label>
          <label>
            CPU 核时
            <input
              type="number"
              min="0"
              value={usageForm.cpu_core_hours}
              onChange={(event) => setUsageForm({ ...usageForm, cpu_core_hours: event.target.value })}
            />
          </label>
          <label>
            内存 GB时
            <input
              type="number"
              min="0"
              value={usageForm.memory_gb_hours}
              onChange={(event) => setUsageForm({ ...usageForm, memory_gb_hours: event.target.value })}
            />
          </label>
          <label>
            存储 GB时
            <input
              type="number"
              min="0"
              value={usageForm.storage_gb_hours}
              onChange={(event) => setUsageForm({ ...usageForm, storage_gb_hours: event.target.value })}
            />
          </label>
          <label>
            网络 GB
            <input
              type="number"
              min="0"
              value={usageForm.network_gb}
              onChange={(event) => setUsageForm({ ...usageForm, network_gb: event.target.value })}
            />
          </label>
          <label>
            利用率
            <input
              type="number"
              min="0"
              max="100"
              value={usageForm.utilization_score}
              onChange={(event) => setUsageForm({ ...usageForm, utilization_score: event.target.value })}
            />
          </label>
          <button className="primary form-submit" disabled={busy}>
            <Database size={17} />
            写入用量
          </button>
        </form>
      </div>
    </section>
  );
}

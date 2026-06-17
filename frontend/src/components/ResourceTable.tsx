import type { Dispatch, FormEvent, SetStateAction } from 'react';
import { PauseCircle, PlayCircle, Search, Trash2 } from 'lucide-react';

import { money } from '../format';
import type { Resource } from '../types';

type ResourceTableProps = {
  resources: Resource[];
  query: string;
  statusFilter: string;
  busy: boolean;
  setQuery: Dispatch<SetStateAction<string>>;
  setStatusFilter: Dispatch<SetStateAction<string>>;
  onSearch: (event: FormEvent) => void;
  onToggleStatus: (resource: Resource) => void;
  onDelete: (resource: Resource) => void;
};

export function ResourceTable({
  resources,
  query,
  statusFilter,
  busy,
  setQuery,
  setStatusFilter,
  onSearch,
  onToggleStatus,
  onDelete
}: ResourceTableProps) {
  return (
    <section className="panel table-panel">
      <div className="panel-head">
        <h2>资源清单</h2>
        <form className="inline-search" onSubmit={onSearch}>
          <div className="search-box">
            <Search size={16} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="名称、负责人、类型"
            />
          </div>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="">全部状态</option>
            <option value="active">active</option>
            <option value="paused">paused</option>
            <option value="retired">retired</option>
          </select>
          <button className="ghost" disabled={busy}>
            <Search size={16} />
            查询
          </button>
        </form>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>名称</th>
              <th>区域</th>
              <th>类型</th>
              <th>负责人</th>
              <th>状态</th>
              <th>预算</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {resources.map((resource) => (
              <tr key={resource.id}>
                <td>{resource.name}</td>
                <td>{resource.region}</td>
                <td>{resource.resource_type}</td>
                <td>{resource.owner}</td>
                <td>
                  <span className={`badge ${resource.status}`}>{resource.status}</span>
                </td>
                <td>{money(resource.monthly_budget)}</td>
                <td>
                  <div className="row-actions">
                    <button
                      className="icon-button"
                      onClick={() => onToggleStatus(resource)}
                      title={resource.status === 'active' ? '暂停' : '启用'}
                    >
                      {resource.status === 'active' ? <PauseCircle size={17} /> : <PlayCircle size={17} />}
                    </button>
                    <button className="icon-button danger" onClick={() => onDelete(resource)} title="删除">
                      <Trash2 size={17} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

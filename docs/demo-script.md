# 演示脚本

## 1. 启动服务

```bash
docker compose up -d --build
docker compose ps
```

打开 `http://localhost:8080`。

## 2. 展示系统总览

页面顶部展示资源总数、活跃资源、近 30 天成本、碳排放、预算风险。说明这些数据来自后端 `/api/analytics/overview`，后端实时从 openGauss 的明细表聚合。

## 3. 新增云资源

在“新增资源”表单输入：

- 名称：`ecs-demo-check`
- 区域：`cn-east-3`
- 类型：`ECS`
- 负责人：`检查演示`
- 月预算：`300`

点击“写入资源”。资源清单增加一行，审计日志出现 `resource_created`。这一步展示前端表单、后端 POST 接口、openGauss 写入。

## 4. 写入用量

在“写入用量”选择刚才新增的资源，填写 CPU、内存、存储、网络和利用率，点击“写入用量”。页面趋势、成本和最近用量刷新。后端会自动估算成本和碳排放。

## 5. 查询、暂停、删除

在资源清单中搜索 `ecs-demo-check`，点击查询。点击暂停图标切换状态，说明调用的是 `PUT /api/resources/{id}`。如需展示删除，点击删除图标，说明后端会级联删除对应资源用量并写审计日志。

## 6. 生成分析快照

点击顶部“聚合”。然后打开 Swagger 或数据库执行：

```sql
select generated_by, total_cost, carbon_kg, snapshot_time
from analytics_snapshots
order by snapshot_time desc
limit 5;
```

可以看到 `generated_by = 'api'` 的快照记录。

## 7. 成本分析演示

点击顶部“分析”。页面会刷新“成本分析”，并把优化建议写入 `cloud_insights` 表。重点展示：

- 7 天成本预测折线区域图。
- 未来 30 天预测成本、预测碳排放、预算压力、可节省金额。
- 优化建议：降配、预算、碳排放、生命周期、异常尖峰。
- 异常成本尖峰：展示实际成本、基线成本和偏离比例。

数据库验证：

```sql
select category, severity, title, estimated_saving, created_at
from cloud_insights
order by impact_score desc
limit 8;
```

## 8. 优化模拟

在优化模拟中修改“当前利用率”和“目标利用率”，点击“开始模拟”。说明后端会按同一套成本和碳排放公式计算优化前后差异，适合现场展示“调整资源利用率后节省多少费用、减少多少碳排放”。

可在 Swagger 中调用：

```text
POST /api/insights/simulate
```

## 9. 告警中心

点击顶部“告警”或运维工作台里的“执行规则”。系统会把预算、异常成本、低利用率和碳排放规则执行结果写入 `cloud_alerts` 表。选择一条告警点击确认图标，状态会变为 `acknowledged`。

数据库验证：

```sql
select severity, alert_type, title, status
from cloud_alerts
order by created_at desc
limit 10;
```

## 10. CSV 批量导入

点击“导入账单/用量 CSV”，选择 `samples/usage-import-sample.csv`。系统会根据 `resource_name` 自动匹配资源；如果资源不存在，会自动创建资源并写入用量记录。

CSV 字段：

```text
resource_name,provider,region,resource_type,owner,monthly_budget,record_date,cpu_core_hours,memory_gb_hours,storage_gb_hours,network_gb,utilization_score
```

这一步可以说明系统不是只能录入单条数据，也能接入批量账单或监控导出数据。

## 11. 自动生成运维周报

点击“周报”或“下载运维周报 Markdown”，浏览器下载 `cloudcostlab-weekly-report.md`。报告内容包含核心指标、告警概况、重点告警、优化建议、异常成本尖峰和下周行动计划。

## 12. 导出 CSV

点击顶部“导出”，浏览器下载 `cloud-resources.csv`。这一步展示后端流式导出能力。

## 13. 可选 Spark 演示

命令行运行：

```bash
docker compose --profile spark run --rm spark-analytics
```

再次查询 `analytics_snapshots`，应出现 `generated_by = 'spark'` 的记录。说明 Spark 通过 JDBC 读取 openGauss 明细数据并写回聚合结果。

## 14. Swagger 接口演示

打开 `http://localhost:8000/docs`，可展示这些接口：

- `GET /api/health`
- `GET/POST /api/resources`
- `GET/POST /api/usage-records`
- `GET /api/analytics/overview`
- `POST /api/analytics/recompute`
- `GET /api/insights/dashboard`
- `POST /api/insights/recompute`
- `POST /api/insights/simulate`
- `GET /api/operations/alerts`
- `POST /api/operations/alerts/recompute`
- `POST /api/operations/import/usage-csv`
- `GET /api/operations/reports/weekly.md`
- `GET /api/audit-log`
- `GET /api/export/resources.csv`

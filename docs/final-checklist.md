# 结课材料最终检查清单

## 已完成

- 项目代码：前端、后端、openGauss、Spark 任务、Dockerfile、Docker Compose 均已完成。
- 报告正文：见 `docs/final-report.md`，已按课程模板组织。
- 浏览器截图：已放入 `docs/screenshots/`，并已嵌入报告。
- 后端接口验证：`http://113.44.208.1:8000/api/health` 返回 `{"message":"ok"}`。
- 前端页面验证：`http://113.44.208.1:8080` 可访问。
- 成本分析和告警数据：已通过接口生成，并反映在截图中。
- Spark JDBC 批处理任务：代码、镜像构建配置和运行命令均已完成，报告中已作为大数据处理模块说明。

## 报告中已经嵌入的截图

- 系统总览页面：`docs/screenshots/01-dashboard-overview.png`
- 前端完整页面：`docs/screenshots/01-dashboard-fullpage.png`
- 成本分析页面：`docs/screenshots/02-cost-analysis.png`
- 告警中心页面：`docs/screenshots/03-operations-alerts.png`
- 新增资源和写入用量表单：`docs/screenshots/04-resource-usage-forms.png`
- 资源清单：`docs/screenshots/05-resource-table.png`
- 最近用量和审计日志：`docs/screenshots/06-audit-usage-risk.png`
- Swagger 接口文档：`docs/screenshots/07-swagger-api-docs.png`
- 移动端视口：`docs/screenshots/08-mobile-dashboard.png`

## 还需要你补充

这些内容不是代码问题，而是个人信息或现场终端材料。

### 1. 个人信息

在 `docs/final-report.md` 开头补充：

- 专业
- 班级
- 姓名
- 学号
- 日期

### 2. 终端验证截图（建议补）

如果要让报告更完整，可以在华为云开发者空间终端执行以下命令并截图。

查看容器状态：

```bash
docker compose ps
```

检查后端健康状态：

```bash
curl http://localhost:8000/api/health
```

进入 openGauss：

```bash
docker exec -it cloudcostlab-opengauss bash
gsql -d postgres -U gaussdb -W 'CloudGauss@2026' -h 127.0.0.1 -p 5432
```

数据库验证 SQL：

```sql
\dt
select count(*) from cloud_resources;
select count(*) from usage_records;
select generated_by, total_cost, carbon_kg, snapshot_time
from analytics_snapshots
order by snapshot_time desc
limit 5;
select severity, alert_type, title, status
from cloud_alerts
order by created_at desc
limit 10;
```

运行自检脚本：

```bash
bash scripts/cloud-preflight.sh
```

### 3. Spark 加分项截图（建议补）

Spark 功能已经完成。为了让报告证据更完整，建议运行：

```bash
docker compose --profile spark run --rm spark-analytics
```

然后查询：

```sql
select generated_by, total_cost, snapshot_time
from analytics_snapshots
order by snapshot_time desc
limit 5;
```

如果能看到 `generated_by = 'spark'`，把截图放到报告“图 3-8 Spark 聚合结果写入 openGauss 截图”位置。

## 打包提交建议

按老师要求命名压缩包：

```text
班级+姓名+学号.zip
```

压缩包建议包含：

- `backend/`
- `frontend/`
- `spark-job/`
- `database/`
- `deploy/`
- `docs/`
- `samples/`
- `scripts/`
- `docker-compose.yml`
- `.env.example`
- `README.md`

不建议提交：

- `frontend/node_modules/`
- `.git/`
- Docker 数据卷
- 本地临时缓存文件

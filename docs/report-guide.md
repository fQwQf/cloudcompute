# 实验报告撰写指南

报告按任务书模板写。建议把项目名写成“基于 openGauss 的云资源成本与碳排放分析平台设计与实现”。

写报告时不要直接复制模板句。建议先把你的华为云部署环境、实际命令输出、截图和遇到的问题填进去，再组织文字。答辩讲解和去 AI 味改写建议见 `docs/defense-notes.md`。

## 1 概述

### 1.1 课程选题背景

写云平台中资源数量多、成本和能耗难以追踪，因此需要一个轻量平台对 ECS、GaussDB、OBS、MRS/Spark 等资源进行统一登记、用量采集、成本估算、碳排放估算和预算风险识别。

### 1.2 课程实验内容

对应任务书逐条写：

- 使用 Docker 部署 openGauss 数据库服务。
- 使用 FastAPI + React 开发前后端分离 Web 应用。
- 后端对 openGauss 进行资源、用量、审计和分析快照的读写。
- 前端和后端分别编写 Dockerfile，并通过 Docker Compose 在华为云开发者空间部署。
- 可选使用 Spark JDBC 对 openGauss 数据进行批量聚合。

## 2 系统设计与实现

### 2.1 系统架构设计

画一张架构图，推荐结构：

```text
浏览器
  |
  | HTTP
  v
Nginx + React 前端容器
  |
  | /api 反向代理
  v
FastAPI 后端容器
  |
  | SQLAlchemy / psycopg2
  v
openGauss 数据库容器

可选：Spark 容器 --JDBC--> openGauss
```

说明前端、后端、数据库、Spark 任务在同一台开发者空间主机上以多个容器运行，形成伪分布式部署。

### 2.2 系统技术选型

可写：

- 数据库：openGauss，负责持久化业务数据和分析快照。
- 后端：FastAPI，提供 REST API；SQLAlchemy 统一数据库访问。
- 前端：React + Vite + Recharts，展示仪表盘、表单、表格和趋势图。
- 容器化：Dockerfile + Docker Compose，保证部署一致性。
- 大数据处理：Spark JDBC 任务，用于批量读取 openGauss 明细表并写入聚合结果。

### 2.3 功能模块设计与实现

建议分模块：

- 资源管理：新增、查询、状态切换、删除，对应 `cloud_resources`。
- 用量采集：写入 CPU、内存、存储、网络等用量，对应 `usage_records`。
- 成本与碳排放估算：后端根据用量自动计算 `estimated_cost` 和 `carbon_kg`。
- 分析聚合：近 30 天成本趋势、资源成本排行、区域成本、预算风险。
- 成本分析：基于近 30 天 openGauss 明细数据进行线性趋势预测、异常尖峰检测和资源优化建议生成。
- 优化模拟：输入 CPU、内存、存储、网络和利用率，估算优化前后成本、碳排放和节省比例。
- 告警中心：根据预算、异常、利用率和碳排放规则生成告警，支持确认告警，形成运维闭环。
- CSV 批量导入：支持导入账单或监控 CSV，自动匹配或创建资源并写入用量记录。
- 运维周报：自动生成 Markdown 周报，沉淀核心指标、告警、建议和行动计划。
- 审计日志：所有新增、修改、删除和聚合操作写入 `audit_events`。
- 导出：资源清单 CSV 导出。
- Spark 聚合：可选批处理写入 `analytics_snapshots`。

放代码截图时重点截：

- `backend/app/models.py` 数据模型。
- `backend/app/services.py` 成本估算和聚合逻辑。
- `backend/app/routes/insights.py` 成本分析接口。
- `frontend/src/App.tsx` 前端调用接口的关键片段。
- `docker-compose.yml` 服务编排。

## 3 应用部署

### 3.1 部署 openGauss / GaussDB

写 Docker Compose 中 `opengauss` 服务，说明：

- 镜像：`docker.m.daocloud.io/enmotech/opengauss:3.0.0`，用于避开直接访问 Docker Hub 的网络问题。
- 环境变量：`GS_USERNAME`、`GS_PASSWORD`、`GS_PORT`。
- 持久化卷：`opengauss_data:/var/lib/opengauss/data`。
- 端口映射：`15432:5432`。

放 `docker compose ps` 截图、openGauss 连接截图、`\dt` 表结构截图。

### 3.2 部署前端/后端应用

写：

```bash
docker compose up -d --build
```

说明后端连接串 `DATABASE_URL`，前端容器通过 Nginx 将 `/api` 代理到后端容器。放前端页面截图、Swagger 截图、容器列表截图。

## 4 测试评估

建议表格：

| 测试项 | 操作 | 预期结果 | 实际结果 |
| --- | --- | --- | --- |
| 后端健康检查 | 访问 `/api/health` | 返回 ok | 通过 |
| 新增资源 | 前端提交资源表单 | 数据写入 openGauss | 通过 |
| 写入用量 | 前端提交用量表单 | 成本和碳排放自动计算 | 通过 |
| 分析聚合 | 点击“聚合” | 写入 `analytics_snapshots` | 通过 |
| 成本分析 | 点击“分析” | 写入 `cloud_insights` 并显示预测/建议 | 通过 |
| 优化模拟 | 修改利用率并提交 | 返回优化前后成本和碳排放 | 通过 |
| 告警中心 | 点击“告警”并确认一条告警 | `cloud_alerts` 写入并更新状态 | 通过 |
| CSV 导入 | 上传样例 CSV | 自动创建资源并写入用量 | 通过 |
| 运维周报 | 点击“周报” | 下载 Markdown 报告 | 通过 |
| CSV 导出 | 点击“导出” | 下载资源清单 | 通过 |
| Spark 任务 | 运行 spark profile | 生成 `generated_by=spark` 快照 | 通过 |

放关键截图：

- 前端总览页。
- 新增资源后资源清单变化。
- 写入用量后趋势图变化。
- 成本分析和优化模拟结果。
- 数据库 SQL 查询结果。
- `pytest` 和 `npm run build` 成功截图。

## 5 总结

### 5.1 项目开发的挑战与应对方法

可写 openGauss 容器首次启动慢、数据库连接需要重试、前后端跨域和容器网络问题、统计口径需要统一。对应写后端启动重试、Nginx 代理、统一服务层聚合函数。

### 5.2 项目部署存在的问题与不足

可写当前是课程演示级部署，openGauss 使用单实例容器模拟伪分布式环境；生产环境应使用主备高可用、密码密钥管理、HTTPS、监控告警。

### 5.3 项目展望与学习心得

可写后续可接入云平台真实账单 API、加入定时 Spark/Flink 任务、增加预测模型、部署到 CCE/Kubernetes。

## 参考文献

可列：

- openGauss Docker 镜像文档。
- FastAPI 官方文档。
- React / Vite 官方文档。
- Spark JDBC 数据源文档。
- 华为云开发者空间文档或课程任务书中的参考资料。

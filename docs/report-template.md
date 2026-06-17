# 实验报告模板

题目：基于 openGauss 的云资源成本与碳排放分析平台设计与实现

专业：

班级：

姓名：

学号：

## 1 概述

### 1.1 课程选题背景

随着云资源规模扩大，ECS、数据库、对象存储和大数据任务会持续产生成本与能耗。传统人工统计方式难以及时发现低利用率资源、预算超支风险和异常成本尖峰。本实验设计并实现一个云资源成本与碳排放分析平台，用 openGauss 保存资源和用量数据，通过 Web 前后端展示成本趋势、预算风险、优化建议和优化模拟结果。

### 1.2 课程实验内容

本实验完成 openGauss 容器化部署，开发 React 前端和 FastAPI 后端，后端通过 SQLAlchemy 对 openGauss 进行读写。系统实现资源管理、用量采集、成本估算、碳排放估算、分析聚合、审计日志、CSV 导出、成本分析、告警中心、CSV 批量导入、运维周报和 Spark JDBC 批处理聚合。

## 2 系统设计与实现

### 2.1 系统架构设计

系统由浏览器、前端容器、后端容器、openGauss 容器和可选 Spark 容器组成。前端通过 Nginx 将 `/api` 请求转发到后端；后端通过数据库连接串访问 openGauss；Spark 任务通过 JDBC 读取明细表并写回聚合快照。

建议插入架构图、容器拓扑图和接口调用流程图。

### 2.2 系统技术选型

- 数据库：openGauss，用于保存资源、用量、分析快照、成本分析结果和审计日志。
- 后端：FastAPI，提供 REST API；SQLAlchemy 负责 ORM 和建表。
- 前端：React + Vite + Recharts，负责仪表盘、表单、表格和图表。
- 容器化：Dockerfile + Docker Compose，支持华为云开发者空间部署。
- 大数据处理：Spark，通过 JDBC 访问 openGauss 并执行批处理聚合。

### 2.3 功能模块设计与实现

资源管理模块实现资源新增、查询、状态切换和删除；用量采集模块记录 CPU、内存、存储、网络和利用率；分析模块按近 30 天数据计算成本趋势、区域成本和预算风险；成本分析模块进行 7 天预测、30 天预算压力估算、异常尖峰检测和优化建议生成；模拟模块根据资源参数计算优化前后成本和碳排放；告警中心根据预算、异常、利用率和碳排放规则生成告警并支持确认；CSV 导入模块支持批量接入账单或监控导出数据；周报模块自动生成 Markdown 运维报告。

建议插入以下代码截图：数据模型、服务层成本公式、成本分析逻辑、前端分析页面、Docker Compose 编排。

## 3 应用部署

### 3.1 部署 openGauss / GaussDB

使用 `docker-compose.yml` 中的 `opengauss` 服务启动数据库，设置 `GS_USERNAME`、`GS_PASSWORD` 和 `GS_PORT`，并通过 Docker volume 持久化 `/var/lib/opengauss/data`。启动命令如下：

```bash
cp .env.example .env
docker compose up -d --build
```

数据库验证命令：

```bash
docker exec -it cloudcostlab-opengauss bash
gsql -d postgres -U gaussdb -W 'CloudGauss@2026' -h 127.0.0.1 -p 5432
```

### 3.2 部署前端/后端应用

后端镜像由 `backend/Dockerfile` 构建，前端镜像由 `frontend/Dockerfile` 构建。前端服务暴露 `8080` 端口，后端服务暴露 `8000` 端口。华为云开发者空间中开放 `8080` 后即可访问系统页面。

建议插入 `docker compose ps`、前端页面、Swagger 页面和数据库表查询截图。

## 4 测试评估

| 测试项 | 操作 | 预期结果 | 实际结果 |
| --- | --- | --- | --- |
| 健康检查 | 访问 `/api/health` | 返回 ok | 通过 |
| 新增资源 | 提交资源表单 | openGauss 新增记录 | 通过 |
| 写入用量 | 提交用量表单 | 自动计算成本和碳排放 | 通过 |
| 分析聚合 | 点击“聚合” | 写入分析快照 | 通过 |
| 成本分析 | 点击“分析” | 生成预测、异常和建议 | 通过 |
| 优化模拟 | 修改参数并提交 | 返回节省金额和减排量 | 通过 |
| 告警中心 | 点击“告警”并确认告警 | 写入并更新 `cloud_alerts` | 通过 |
| CSV 导入 | 上传样例 CSV | 自动创建资源并写入用量 | 通过 |
| 运维周报 | 点击“周报” | 下载 Markdown 报告 | 通过 |
| Spark 聚合 | 运行 Spark 容器 | 写入 `generated_by=spark` 快照 | 通过 |

建议插入测试命令截图：

```bash
PYTHONPATH=backend pytest backend/tests
cd frontend && npm run build
docker compose config
```

## 5 总结

### 5.1 项目开发的挑战与应对方法

开发过程中主要挑战包括 openGauss 容器初始化较慢、前后端容器网络通信、成本和碳排放统计口径统一、图表数据实时刷新。项目通过后端启动重试、Nginx 反向代理、服务层统一计算函数和前端集中刷新机制解决这些问题。

### 5.2 项目部署存在的问题与不足

当前系统主要用于课程演示，openGauss 采用单实例容器部署，生产环境还需要主备高可用、备份恢复、密钥管理、HTTPS 和监控告警。成本公式为估算模型，实际生产应接入云厂商账单和能耗数据。

### 5.3 项目展望与学习心得

后续可以接入华为云真实账单 API，使用定时 Spark/Flink 任务实现周期性分析，引入机器学习预测模型，并部署到 CCE/Kubernetes。通过本实验加深了对容器化、openGauss、前后端分离和云资源治理的理解。

## 参考文献

按学校格式列出 openGauss、FastAPI、React、Vite、Spark JDBC、Docker 和华为云开发者空间相关文档。

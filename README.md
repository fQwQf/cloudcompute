# CloudCostLab 云资源成本与碳排放分析平台

本项目用于《大数据与云计算技术》期末实验：容器化部署 openGauss/GaussDB 数据库，开发前后端分离 Web 应用，并通过 Dockerfile/Compose 在华为云开发者空间完成部署演示。

## 项目亮点

- 前后端分离：React + Vite 前端、FastAPI 后端、Nginx 反向代理。
- openGauss 读写：资源、用量、聚合快照、审计日志全部落库。
- 完整业务闭环：资源 CRUD、用量采集、成本估算、碳排放估算、预算风险、CSV 导出。
- 成本分析亮点：7 天成本预测、30 天预算压力、异常成本尖峰检测、资源降配建议、节省潜力估算。
- 现场互动亮点：优化模拟，调整 CPU、内存、网络和利用率后实时计算优化收益。
- 实用运维亮点：告警中心、告警确认、CSV 账单/用量批量导入、自动生成 Markdown 运维周报。
- 大数据加分项：`spark-job/` 提供 Spark JDBC 任务，从 openGauss 读取明细并写回聚合快照。
- 容器化交付：`backend/Dockerfile`、`frontend/Dockerfile`、`docker-compose.yml`。
- 可演示性：后端启动自动建表和生成演示数据，前端所有按钮均对应后端 API。

## 目录结构

```text
backend/              FastAPI 后端
frontend/             React 前端
spark-job/            可选 Spark JDBC 聚合任务
database/schema.sql   openGauss 表结构参考
deploy/k8s/           可选 Kubernetes 部署清单
docs/                 部署、演示、报告说明
scripts/              华为云部署前自检脚本
docker-compose.yml    本地/开发者空间一键部署
```

## 快速启动

```bash
cp .env.example .env
docker compose up -d --build
```

默认镜像已改为国内镜像站，其中 openGauss 默认使用 `docker.m.daocloud.io/enmotech/opengauss:3.0.0`。如果所在网络无法访问该镜像站，修改 `.env` 中的 `OPENGAUSS_IMAGE`、`PYTHON_IMAGE`、`NODE_IMAGE`、`NGINX_IMAGE`、`SPARK_IMAGE` 后重新执行上面的命令。

访问：

- 前端：http://localhost:8080
- 后端 Swagger：http://localhost:8000/docs
- openGauss：宿主机 `localhost:15432`，容器网络 `opengauss:5432`

停止：

```bash
docker compose down
```

清空数据库卷：

```bash
docker compose down -v
```

更多步骤见 [docs/deployment-guide.md](docs/deployment-guide.md)。
接口演示请求见 [docs/api-examples.http](docs/api-examples.http)。

部署后建议先运行自检：

```bash
bash scripts/cloud-preflight.sh
```

## 演示入口

推荐按 [docs/demo-script.md](docs/demo-script.md) 操作。核心演示顺序：

1. 打开前端总览页，展示 openGauss 中的资源和统计数据。
2. 新增资源，刷新资源清单和审计日志。
3. 写入用量，展示成本、碳排放、趋势图变化。
4. 点击“分析”，生成预测、异常检测和优化建议并写入 openGauss。
5. 点击“告警”，执行预算、异常、利用率和碳排放告警规则，并确认一条告警。
6. 使用优化模拟现场调整参数，展示节省金额和碳减排量。
7. 导入 [samples/usage-import-sample.csv](samples/usage-import-sample.csv)，展示批量账单/用量数据接入。
8. 下载 Markdown 运维周报，展示系统可输出管理报告。
9. 点击“聚合”，生成分析快照并写回 openGauss。
10. 导出 CSV，展示后端数据导出接口。
11. 可选运行 Spark 聚合任务：`docker compose --profile spark run --rm spark-analytics`。

## 测试

后端单元测试：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=. pytest
```

前端构建测试：

```bash
cd frontend
npm install
npm run build
```

## 报告写法

按任务书模板撰写即可，具体章节内容、截图建议和可复用文字见 [docs/report-guide.md](docs/report-guide.md)。
可直接套用的报告骨架见 [docs/report-template.md](docs/report-template.md)。

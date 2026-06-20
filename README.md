# CloudCostLab 云资源成本与碳排放分析平台

本项目是《大数据与云计算技术》课程结课实验。系统基于 Docker Compose 部署 openGauss、FastAPI 后端、React 前端和 Spark JDBC 批处理任务，实现云资源登记、用量写入、成本与碳排放估算、预算风险分析、告警、CSV 导入导出和周报生成。

如华为云实例未欠费停机，在线演示地址为 `http://113.44.208.1:8080`，接口文档地址为 `http://113.44.208.1:8000/docs`。

## 目录结构

```text
backend/                 FastAPI 后端服务
frontend/                React + Vite 前端
spark-job/               Spark JDBC 聚合任务
database/schema.sql      openGauss 表结构参考
samples/                 CSV 导入样例
scripts/                 部署自检脚本
docs/                    部署指南、演示脚本、API 示例、报告源文件和截图
latex-report/            LaTeX 报告源码和模板依赖
docker-compose.yml       容器编排文件
.env.example             部署环境变量模板
```

最终 PDF 报告位于根目录：`特软班-童济舟-2024302111261-云计算技术课程实验报告.pdf`。

课程任务书保留一份 PDF：`docs/course-requirement.pdf`。

## 快速部署

```bash
cp .env.example .env
docker compose up -d --build
```

默认镜像已配置为国内镜像站，适合无法直接访问 Docker Hub 的环境：

- openGauss：`docker.m.daocloud.io/enmotech/opengauss:3.0.0`
- Python、Node、Nginx、Spark：通过 `.env.example` 中的镜像变量配置
- pip、npm、Maven 依赖：默认使用国内源

访问地址：

- 前端页面：`http://localhost:8080`
- 后端 Swagger：`http://localhost:8000/docs`
- openGauss：宿主机 `localhost:15432`，容器网络 `opengauss:5432`

部署完成后建议运行：

```bash
bash scripts/cloud-preflight.sh
```

更完整的华为云部署说明见 [docs/deployment-guide.md](docs/deployment-guide.md)。

## 演示顺序

推荐按 [docs/demo-script.md](docs/demo-script.md) 演示：

1. 打开前端总览页，说明指标来自 openGauss。
2. 新增资源，查看资源清单和审计日志。
3. 写入用量，展示成本、碳排放和趋势变化。
4. 点击“聚合”，生成 `analytics_snapshots` 快照。
5. 点击“分析”，生成预测、异常检测和优化建议。
6. 执行告警规则并确认一条告警。
7. 导入 `samples/usage-import-sample.csv`。
8. 下载 Markdown 运维周报和资源 CSV。
9. 运行 Spark 任务：`docker compose --profile spark run --rm spark-analytics`。

## 本地验证

后端测试：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=. pytest
```

前端构建：

```bash
cd frontend
npm install
npm run build
```

## 报告与材料

- 最终 PDF：`特软班-童济舟-2024302111261-云计算技术课程实验报告.pdf`
- Markdown 报告源：[docs/final-report.md](docs/final-report.md)
- LaTeX 报告源：[latex-report/main.tex](latex-report/main.tex)
- 截图目录：[docs/screenshots/](docs/screenshots/)
- 课程任务书：[docs/course-requirement.pdf](docs/course-requirement.pdf)

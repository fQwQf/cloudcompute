# 部署说明

## 1. 环境要求

- Docker 24+，Docker Compose v2。
- 至少 4GB 可用内存；首次拉取 openGauss 和构建前端镜像需要联网。
- 默认端口：`8080` 前端、`8000` 后端、`15432` openGauss。

## 2. 本地或华为云开发者空间部署

进入项目根目录：

```bash
cp .env.example .env
docker compose up -d --build
```

国内环境无法直接访问 Docker Hub 时，本项目默认已经使用镜像站：

```env
OPENGAUSS_IMAGE=docker.m.daocloud.io/enmotech/opengauss:3.0.0
PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.13-slim
NODE_IMAGE=docker.m.daocloud.io/library/node:22-alpine
NGINX_IMAGE=docker.m.daocloud.io/library/nginx:1.27-alpine
SPARK_IMAGE=docker.m.daocloud.io/bitnami/spark:3.5
```

如果该镜像站临时不可用，只需要编辑 `.env` 里的这些镜像变量，换成学校或华为云环境可访问的镜像地址。后端 `pip`、前端 `npm`、Spark JDBC jar 也默认使用国内源：

```env
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
NPM_REGISTRY=https://registry.npmmirror.com
POSTGRES_JDBC_URL=https://maven.aliyun.com/repository/public/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar
```

修改 `.env` 后重新构建：

```bash
docker compose down
docker compose up -d --build
```

建议先单独验证 openGauss 镜像能否拉取：

```bash
docker pull docker.m.daocloud.io/enmotech/opengauss:3.0.0
```

如果仍然返回 `403 Forbidden` 或超时，可以尝试把 `.env` 中的 `OPENGAUSS_IMAGE` 改为你当前网络可访问的镜像，例如学校私有镜像仓库、华为云 SWR 私有仓库，或先在能访问外网的机器上执行：

```bash
docker pull enmotech/opengauss:3.0.0
docker tag enmotech/opengauss:3.0.0 swr.cn-north-4.myhuaweicloud.com/你的组织/opengauss:3.0.0
docker push swr.cn-north-4.myhuaweicloud.com/你的组织/opengauss:3.0.0
```

然后在 `.env` 中写：

```env
OPENGAUSS_IMAGE=swr.cn-north-4.myhuaweicloud.com/你的组织/opengauss:3.0.0
```

查看启动状态：

```bash
docker compose ps
docker compose logs -f opengauss backend frontend
```

后端会等待数据库可连接，自动创建表并写入演示数据。openGauss 首次初始化可能需要 1 到 3 分钟。

检查前建议运行自检脚本：

```bash
bash scripts/cloud-preflight.sh
```

如果脚本提示前端、后端、数据库都可访问，再进行现场演示会更稳。

访问地址：

- 前端页面：`http://localhost:8080`
- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/health`

在华为云开发者空间中，把端口 `8080` 暴露为 Web 访问端口即可演示前端；如需展示接口文档，再暴露 `8000`。

## 3. openGauss 验证

进入数据库容器：

```bash
docker exec -it cloudcostlab-opengauss bash
```

连接数据库：

```bash
gsql -d postgres -U gaussdb -W 'CloudGauss@2026' -h 127.0.0.1 -p 5432
```

常用检查 SQL：

```sql
\dt
select count(*) from cloud_resources;
select count(*) from usage_records;
select * from analytics_snapshots order by snapshot_time desc limit 5;
select category, severity, title from cloud_insights order by created_at desc limit 5;
select severity, alert_type, title, status from cloud_alerts order by created_at desc limit 5;
select event_type, message, created_at from audit_events order by created_at desc limit 10;
```

宿主机也可以通过 `localhost:15432` 连接。默认账号密码在 `.env.example` 中，生产环境应修改密码。

## 4. 前后端镜像

单独构建镜像：

```bash
docker build -t cloudcostlab-backend:latest ./backend
docker build -t cloudcostlab-frontend:latest ./frontend
```

如果单独构建也需要指定镜像站：

```bash
docker build \
  --build-arg PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.13-slim \
  --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
  -t cloudcostlab-backend:latest ./backend

docker build \
  --build-arg NODE_IMAGE=docker.m.daocloud.io/library/node:22-alpine \
  --build-arg NGINX_IMAGE=docker.m.daocloud.io/library/nginx:1.27-alpine \
  --build-arg NPM_REGISTRY=https://registry.npmmirror.com \
  -t cloudcostlab-frontend:latest ./frontend
```

查看镜像：

```bash
docker images | grep cloudcostlab
```

## 5. Spark 加分项

后端启动并建表后运行：

```bash
docker compose --profile spark run --rm spark-analytics
```

该任务会通过 JDBC 从 `cloud_resources` 和 `usage_records` 读取数据，用 Spark 聚合成本、利用率、碳排放、预算风险，并把结果追加写入 `analytics_snapshots`，`generated_by` 字段为 `spark`。

验证：

```bash
docker exec -it cloudcostlab-opengauss bash
gsql -d postgres -U gaussdb -W 'CloudGauss@2026' -h 127.0.0.1 -p 5432 \
  -c "select generated_by, total_cost, snapshot_time from analytics_snapshots order by snapshot_time desc limit 5;"
```

## 6. 可选 Kubernetes 部署

先构建镜像，并按实际镜像仓库修改 `deploy/k8s/*.yaml` 中的 `image` 字段：

```bash
docker build -t cloudcostlab-backend:latest ./backend
docker build -t cloudcostlab-frontend:latest ./frontend
kubectl apply -f deploy/k8s/opengauss.yaml
kubectl apply -f deploy/k8s/backend.yaml
kubectl apply -f deploy/k8s/frontend.yaml
```

前端 NodePort 默认为 `30080`。如果部署在华为云 CCE 或开发者空间的 Kubernetes 环境中，需要按平台提示开放访问端口。

## 7. 常见问题

`backend` 日志中短时间出现数据库连接失败：openGauss 首次初始化较慢，后端有重试逻辑，等待后再次查看日志。

端口占用：修改 `docker-compose.yml` 左侧宿主机端口，例如 `"18080:80"`。

密码修改：同时修改 `.env` 中 `OPENGAUSS_PASSWORD` 和 `DATABASE_URL`。连接串中的特殊字符要 URL 编码，例如 `@` 写成 `%40`。

# 工业AI质检与时序分析平台

Industrial AI Quality Inspection & Timeseries Analysis Platform

基于 FastAPI + React + Ant Design 的工业质检与时序数据分析平台，支持设备管理、缺陷检测、时序异常分析、RBAC 权限控制等功能。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11、FastAPI、SQLAlchemy (async)、Uvicorn |
| 前端 | React 18、Vite、Ant Design 5、ECharts |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| 认证 | JWT + RBAC 角色权限 |
| 部署 | Docker、Docker Compose |

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # API 路由
│   │   ├── core/               # 配置、数据库、安全、异常
│   │   ├── middleware/          # 审计日志、限流中间件
│   │   ├── models/             # ORM 模型
│   │   ├── schemas/            # Pydantic 数据模型
│   │   ├── services/           # 业务逻辑
│   │   └── main.py             # 应用入口
│   ├── requirements.txt
│   ├── seed_data.py            # 假数据填充脚本
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/              # 页面组件
│   │   ├── layouts/            # 布局组件
│   │   ├── api.js              # Axios 请求封装
│   │   ├── App.jsx             # 路由配置
│   │   └── main.jsx            # 入口
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## 快速启动（本地开发）

### 1. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt
# 注意：如遇 bcrypt 兼容问题，执行：
pip install "bcrypt==4.0.1"

# 启动服务（首次启动会自动建表和初始化数据）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

后端启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动后访问：http://localhost:5173

### 3. 填充假数据（可选）

```bash
cd backend
python seed_data.py
```

会写入生产线、设备、批次、缺陷样本、时序数据等测试数据。

## Docker 一键部署

```bash
docker-compose up -d --build
```

启动后访问：http://localhost

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | Admin@123456 | 超级管理员 |

## 功能模块

- **仪表盘** — 设备统计、缺陷趋势、时序概览
- **设备管理** — 设备CRUD、状态监控、健康评分
- **生产线管理** — 生产线配置、批次追踪
- **缺陷检测** — 样本上传、AI检测、结果查看
- **时序分析** — 数据模拟、Z-Score 异常检测、趋势图表
- **通知中心** — 告警通知、已读管理
- **审计日志** — 操作记录自动追踪

## API 端点概览

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth/*` | 登录、注册、刷新令牌 |
| 用户 | `/api/v1/users/*` | 用户管理 |
| 设备 | `/api/v1/industrial/devices/*` | 设备 CRUD |
| 生产线 | `/api/v1/industrial/production-lines/*` | 生产线管理 |
| 缺陷 | `/api/v1/defects/*` | 缺陷样本与检测 |
| 时序 | `/api/v1/timeseries/*` | 时序数据与异常分析 |
| 仪表盘 | `/api/v1/dashboard/*` | 统计数据 |
| 通知 | `/api/v1/notifications/*` | 通知管理 |

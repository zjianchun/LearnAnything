# 部署指南

## 前置条件

- Docker + Docker Compose
- cloudflared（Cloudflare 隧道客户端）
- Git

## 部署步骤

```bash
# 1. 克隆仓库
git clone git@github.com:zjianchun/LearnAnything.git
cd LearnAnything

# 2. 配置环境变量
cp .env.example .env
vim .env  # 填入 MINIMAX_API_KEY

# 3. 启动
docker compose up -d --build

# 4. 验证
curl http://127.0.0.1:8088/api/graph/subjects
# 应返回9科JSON

# 5. 配置 cloudflared 隧道
cloudflared tunnel --url http://127.0.0.1:8088
# 或使用已有隧道配置
```

## 首次启动

首次启动时 backend 会自动：
1. 创建 SQLite 数据库
2. 应用 schema
3. 加载题库数据

无需手动 seed。

## 更新

```bash
cd LearnAnything
git pull
docker compose up -d --build
```

## 目录结构（服务器上）

```
LearnAnything/
├── data/           → 挂载到 backend + nginx
│   ├── math/       → 题库JSON
│   ├── physics/
│   ├── exam-pages/ → 试卷截图(nginx直接serve)
│   └── ...
├── courseware/     → 挂载到 nginx 直接serve
├── backend/       → FastAPI容器
├── frontend/      → Vue构建→nginx容器
├── docker-compose.yml
├── nginx.conf
└── .env
```

## 端口

| 服务 | 内部端口 | 外部 |
|------|---------|------|
| nginx | 80 | 127.0.0.1:8088 |
| backend | 8000 | 仅内部 |
| frontend | 80 | 仅内部 |
| cloudflared | — | 公网HTTPS |

## 常用命令

```bash
# 查看日志
docker compose logs -f backend
docker compose logs -f nginx

# 重启单个服务
docker compose restart backend

# 重建数据库（慎用）
docker compose exec backend rm /app/db/learn.db
docker compose restart backend
```

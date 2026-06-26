# LearnAnything 📚

初二定制化辅导系统 — 替代课外辅导班的自用学习平台。

## 功能

- 🎯 **学情诊断** — 按知识点粒度定位薄弱环节，自动回溯前置知识
- 📖 **互动课件** — 带语音讲解的互动教学页（基于TeachAny）
- ✏️ **智能练习** — 根据掌握度自动选题，错因诊断
- 📝 **错题本** — 遗忘曲线复习，变式训练
- 📊 **家长看板** — 每日学习报告，进度可视化
- 🗓️ **学习计划** — 自动生成每日计划

## 技术栈

- 后端：Python FastAPI + SQLite
- 前端：Vue 3 + Vite + TypeScript
- 部署：Docker Compose + Nginx
- TTS：Edge TTS（微软神经语音）
- AI学伴：MiniMax M3

## 快速部署

```bash
# 克隆
git clone git@github.com:zjianchun/LearnAnything.git
cd LearnAnything

# 配置API Key
cp .env.example .env
# 编辑 .env 填入 MINIMAX_API_KEY

# 启动
docker compose up -d

# 导入数据
docker compose exec backend python /app/../tools/seed_data.py
```

访问 `http://your-server-ip` 即可使用。

## 目录结构

```
├── backend/          # FastAPI 后端
├── frontend/         # Vue 3 前端
├── courseware/       # TeachAny 互动课件
├── data/            # 知识图谱 + 题库数据
│   ├── math/        # 数学
│   ├── physics/     # 物理
│   └── english/     # 英语
├── tools/           # 数据导入工具
├── docker-compose.yml
└── nginx.conf
```

## 学科覆盖

- **数学**：初一回溯 + 初二全册 + 初三（持续扩充）
- **物理**：初二全册 + 初三（待扩充）
- **英语**：初二全册 + 初三（待扩充）

教材版本：人教版（武汉市）

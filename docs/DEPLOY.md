# 服务器部署步骤（逐步操作）

## 前提

- 一台 Linux 服务器（Ubuntu 20.04+ 或 Debian 11+）
- 有 root 或 sudo 权限
- 服务器能访问外网（GitHub + MiniMax API）

---

## 第一步：安装 Docker

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker

# 安装 Docker Compose (如果 docker compose 命令不可用)
sudo apt install -y docker-compose-plugin

# 验证
docker --version
docker compose version
```

---

## 第二步：安装 Git 并克隆仓库

```bash
sudo apt install -y git

# 克隆（仓库约1.7GB，含课件和题库数据）
cd /opt
sudo git clone https://github.com/zjianchun/LearnAnything.git
cd LearnAnything

# 如果用SSH:
# sudo git clone git@github.com:zjianchun/LearnAnything.git
```

---

## 第三步：配置环境变量

```bash
cp .env.example .env
nano .env
```

填入内容：
```
MINIMAX_API_KEY=sk-cp-E-qOnaRqHhOPp4cV6otZsf74wyx49skP4QRRYDLpMNoNwRmOuDByC6GntcQ3-Pizalk-kM3xiJxbqT-aRe3U1cQdGcPDMyhQenygUFDEQe40Ki_DUaHYBlA
OPENAI_API_BASE=https://api.minimax.chat/v1
```

---

## 第四步：构建并启动

```bash
# 构建所有镜像（首次约3-5分钟）
docker compose up -d --build

# 查看是否都启动了
docker compose ps
```

应该看到3个容器都是 `running`：
```
NAME                STATUS
learnany-backend    running
learnany-frontend   running
learnany-nginx      running
```

---

## 第五步：初始化数据库

```bash
# 进入 backend 容器执行 seed
docker compose exec backend python seed.py
```

如果报错找不到 seed.py，手动初始化：
```bash
# 在容器外用 tools/seed_data.py
docker compose exec backend python -c "
import sqlite3, json
from pathlib import Path

DB_PATH = Path('/app/db/learn.db')
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(str(DB_PATH))
schema = Path('/app/db/schema.sql').read_text()
conn.executescript(schema)

# 加载题目
total = 0
for qf in Path('/app/data').rglob('questions-*.json'):
    qs = json.loads(qf.read_text())
    for q in qs:
        try:
            conn.execute(
                'INSERT OR IGNORE INTO questions (id,node_id,type,difficulty,question,options,correct_answer,hint,steps) VALUES (?,?,?,?,?,?,?,?,?)',
                (q.get('id'),q.get('node_id'),q.get('type','choice'),q.get('difficulty',1),
                 q.get('question',''),json.dumps(q.get('options',[]),ensure_ascii=False),
                 q.get('correct_answer',''),q.get('hint',''),json.dumps(q.get('steps',[]),ensure_ascii=False))
            )
            total += 1
        except: pass
conn.commit()
conn.close()
print(f'Done: {total} questions loaded')
"
```

---

## 第六步：验证服务

```bash
# 测试后端API
curl http://127.0.0.1:8088/api/graph/subjects
# 应返回JSON，包含9个学科

# 测试前端页面
curl -s http://127.0.0.1:8088/ | head -5
# 应返回HTML (含 <div id="app">)

# 测试课件
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8088/courseware/_assets/scripts/teachany-kg-manifest.json
# 应返回 200
```

---

## 第七步：配置 cloudflared 隧道

```bash
# 安装 cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# 登录（会打开浏览器授权）
cloudflared tunnel login

# 创建隧道
cloudflared tunnel create learnanything

# 配置隧道
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: learnanything
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: your-domain.com
    service: http://127.0.0.1:8088
  - service: http_status:404
EOF

# 添加 DNS 记录
cloudflared tunnel route dns learnanything your-domain.com

# 启动隧道（作为系统服务）
cloudflared service install
systemctl start cloudflared
systemctl enable cloudflared
```

如果不需要自定义域名，直接用临时隧道测试：
```bash
cloudflared tunnel --url http://127.0.0.1:8088
# 会输出一个 https://xxx.trycloudflare.com 链接
```

---

## 第八步：确认一切正常

在浏览器打开你的域名（或临时链接），检查：

- [ ] 首页显示"今日学习计划"+ 任务卡片
- [ ] 导航栏有：全科图谱/知识地图/学习路径/课件库/PBL探究/记忆/诊断/练习/错题本/进度
- [ ] `/graph` 显示9科卡片
- [ ] `/library` 显示课件列表
- [ ] `/practice` 能做题，公式正常渲染
- [ ] `/parent` 能看到家长面板

---

## 常见问题

### 前端显示空白或旧版本
```bash
# 强制重新构建前端
docker compose build --no-cache frontend
docker compose up -d
# 浏览器 Ctrl+Shift+R 强制刷新
```

### 后端报错
```bash
docker compose logs backend
```

### 数据库重置
```bash
docker compose exec backend rm -f /app/db/learn.db
docker compose restart backend
# 重新执行第五步
```

### 更新代码
```bash
cd /opt/LearnAnything
git pull
docker compose up -d --build
```

### 查看磁盘占用
```bash
du -sh /opt/LearnAnything/data/
du -sh /opt/LearnAnything/courseware/
docker system df
```

---

## 端口映射

```
外部 HTTPS (cloudflared)
  → 127.0.0.1:8088 (nginx)
    → backend:8000 (FastAPI, /api/*)
    → frontend:80  (Vue SPA, /*)
    → 静态文件     (/courseware/*, /exam-pages/*)
```

nginx 只监听 127.0.0.1:8088，不对外暴露，安全由 cloudflared + Cloudflare 边缘处理。

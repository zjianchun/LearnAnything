# 个性化全科学习平台 · 技术方案

> 项目代号：LearnAnything（基于 TeachAny Skill 与官方课标/课件深度复用）
> 版本：v2.0 · 2026-06-26（全科 + teachany.cn 形态扩展）
> 目标：完全替代课外辅导班，一个学生从初二用到中考；形态对标 teachany.cn，但为单用户个性化

---

## 〇、v2.0 范围说明（相对 v1.0 的变化）

v1.0 是"数理英 3 科 + 精简单用户"。v2.0 扩展为**接近 teachany.cn 形态的个性化全科平台**，全部要做、不做减法：

| 维度 | v1.0 | v2.0（当前） |
|:---|:---|:---|
| 学科 | 数/理/英 3 科 | **初中全科 10 科**（语数英物化生地史道法心理） |
| 知识结构 | 手写数学树 | **TeachAny 官方课标树**（10 科，权威 node_id + prerequisites + 课标点 + 教材章节） |
| 课件 | 留空 | **复用 TeachAny 课件**，自托管成静态文件 |
| 形态 | 诊断+练习+错题本 | + **知识地图 / 全科图谱 / 学习路径 / PBL / 阅读学院 / 课件库** |

**核心定位区别**：teachany.cn 是面向所有人的公开课件门户；本系统是面向 1 个学生的**私有个性化平台**——复用 teachany.cn 的课标树与课件，叠加该生的诊断/掌握度/路径，所有视图都带"这个孩子"的学情色彩。

**关键架构原则（务必遵守，避免再次跑偏）**：
1. **不编造 node_id**——一律用 TeachAny 官方 `find_nodes.py` / 官方树的 node_id
2. **课件复用而非重造**——已有的从 teachany.cn 取，缺的用 TeachAny Skill 按完整模式生成
3. **课件提前生成、自托管为静态文件**——运行时服务器不跑 agent，只伺服静态页 + 自建 API
4. **TeachAny Skill 是"制作时"工具**（在开发环境用来产课件），不部署到服务器

---

## 一、系统定位

| 项 | 说明 |
|:---|:-----|
| 用户 | 1名初二学生（武汉，人教版），9月升初三 |
| 学科 | 初中全科 10 科（语文/数学/英语/物理/化学/生物/地理/历史/道法/心理），主攻数理英，其余按需 |
| 数据源 | TeachAny 官方课标树（cn/middle/*.json）+ 官方课件 + 武汉中考考频校准 |
| 形态 | 知识地图 · 全科图谱 · 学习路径 · 诊断 · 练习 · 错题本 · PBL · 阅读学院 · 课件库 · 家长看板 |
| 生命周期 | 2026年7月 → 2027年6月中考，持续约12个月 |
| 部署 | 自有服务器（cloudflared 隧道，端口8088），联网设备均可访问 |
| 开发 | 全栈，AI辅助生成代码；课件用 TeachAny Skill 生成 |

---

## 一·B、功能模块全景（teachany.cn 形态）

| 模块 | 说明 | 数据/能力来源 |
|:---|:---|:---|
| **知识地图** | 单学科节点图 + prerequisites 依赖连线 + 该生掌握度红黄绿 | 官方树 + 本系统学情 |
| **全科图谱** | 跨 10 学科总览，一屏看到全科结构与进度 | 官方 10 科树 + 学情 |
| **学习路径** | 按依赖+掌握度+学校进度生成的个性化路径（path） | 官方 prerequisites + 学情 |
| **诊断** | 入学诊断卷 + 实时掌握度 + 前置回溯（可跨年级到初一） | 题库 + 官方依赖图 |
| **练习** | 智能选题（按掌握度分配难度）+ 错因诊断 | 题库 + 选题引擎 |
| **错题本** | 遗忘曲线复习（1/3/7/15天）+ 变式 | 本系统 |
| **课件库** | 可浏览的课件列表（本系统形式呈现），点开即学 | TeachAny 课件（自托管） |
| **课件学习页** | 互动课件 + TTS 语音 + AI 学伴 | TeachAny 生成 |
| **PBL 探究路径** | 项目式学习路径 | TeachAny PBL（pbl.html / API）或自建 |
| **阅读学院** | 语文阅读专题模块（具体形态实现时对照 teachany.cn 细化） | TeachAny 语文树/阅读资源 |
| **家长看板** | 每日报告、周趋势、薄弱点提醒 | 本系统 daily_stats |

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    浏览器（学生端 / 家长端）                    │
│  学生：学习主界面、做题、看讲解、AI问答                         │
│  家长：学情看板、每日报告、进度趋势                             │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────▼────────────────────────────────┐
│                      Nginx 反向代理                           │
│                   （SSL + 静态资源托管）                       │
└──────┬─────────────────────────────────────────┬────────────┘
       │                                         │
┌──────▼──────────┐                    ┌─────────▼───────────┐
│  API 服务 (后端)  │                    │  静态课件 (TeachAny) │
│  Python FastAPI  │                    │  HTML/JS/TTS 音频    │
│                  │                    │                     │
│  - 学情诊断      │                    │  - 互动教学页        │
│  - 学习路径      │                    │  - Canvas 仿真      │
│  - 题库/组卷     │                    │  - 语音讲解         │
│  - 评估/报告     │                    │  - AI 学伴          │
│  - TTS 生成      │                    │                     │
└──────┬──────────┘                    └─────────────────────┘
       │
┌──────▼──────────┐
│   数据层         │
│  SQLite + JSON   │
│                  │
│  - 知识图谱      │
│  - 学情记录      │
│  - 题库          │
│  - 学习计划      │
└─────────────────┘
```

### 技术选型

| 层 | 选型 | 理由 |
|:---|:-----|:-----|
| 前端 | Vue 3 + Vite | 轻量、响应式、单人项目够用 |
| 后端 | Python FastAPI | 与TeachAny脚本生态一致（Python），异步性能好 |
| 数据库 | SQLite | 单用户无需MySQL/PG，备份就是复制文件 |
| 课件层 | TeachAny HTML（静态） | 直接复用其互动课件生成能力 |
| TTS | Edge TTS（微软神经语音） | TeachAny已集成，免费、中文质量最好 |
| AI学伴 | OpenAI API / 本地Ollama | 答疑用，可选本地部署降低成本 |
| 部署 | Docker Compose | 一键启动，迁移方便 |
| 反代 | Nginx / Caddy | HTTPS + 静态资源 |

---

## 三、模块设计

### 3.1 知识图谱模块

核心数据结构——**知识点依赖图**：

```
初一.有理数运算 ──→ 初一.一元一次方程 ──→ 初二.一次函数
                                          ↓
初一.平面几何基础 ──→ 初二.三角形 ──→ 初二.全等三角形
                                          ↓
                                     初三.相似三角形
```

数据来源：
- TeachAny 知识树（2394个节点，已有prerequisites字段）
- 人教版初中教材目录（按章节对应）
- 武汉中考考纲（标注考频和分值）

每个知识点的元数据：
```json
{
  "node_id": "math-m-linear-function",
  "name": "一次函数",
  "subject": "math",
  "grade": 8,
  "semester": 1,
  "textbook_chapter": "人教版八上·第11章",
  "prerequisites": ["math-m-proportional-function", "math-m-coordinate-system"],
  "exam_weight": "high",
  "exam_points": "10-12",
  "difficulty": 2,
  "estimated_hours": 4,
  "status": "not_started"
}
```

### 3.2 学情诊断模块

**诊断流程：**

```
首次使用                          日常使用
   │                                │
   ▼                                ▼
[入学诊断卷]                   [每次做题自动记录]
 按知识点出题                       │
 每点2-3题                          ▼
   │                         [实时更新掌握度]
   ▼                                │
[生成知识点掌握度地图]               ▼
 ● 绿色=掌握(>80%)           [发现新薄弱点]
 ● 黄色=半会(50-80%)               │
 ● 红色=不会(<50%)                 ▼
   │                         [自动追溯前置知识]
   ▼                          是前置没学好？
[自动追溯]                     还是本点没理解？
 一次函数不会 →
 检测：正比例函数会不会？
      坐标系会不会?
```

**掌握度算法：**

```python
# 简化版：基于最近N次做题记录，加权计算
def calc_mastery(records: list[Record]) -> float:
    """
    - 最近的题权重更高（遗忘曲线）
    - 难度越高的题答对加分越多
    - 连续答对加速提升，连续答错触发回溯
    """
    recent = records[-10:]  # 取最近10次
    weights = [0.5 + 0.5 * (i / len(recent)) for i in range(len(recent))]
    score = sum(r.correct * w * r.difficulty_weight for r, w in zip(recent, weights))
    return score / sum(weights)
```

**前置知识回溯逻辑：**
- 某知识点掌握度 < 50%
- 检查其 prerequisites 列表
- 对每个前置知识点出2道诊断题
- 如果前置也不会 → 先学前置（可能回溯到初一）
- 回溯深度上限：2层（避免无限回溯）

---

### 3.3 学习路径与方案生成

**路径生成原则：**
1. 先补前置缺口，再攻当前内容
2. 跟学校进度走：周一到周五预习/同步，周末补旧账
3. 三科交替，避免单科疲劳
4. 每个知识点：讲解 → 练习 → 测试 → 通过才进下一个

**每日学习计划自动生成示例：**

```
┌─────────────────────────────────────────┐
│ 2026年7月15日（周三）学习计划            │
├─────────────────────────────────────────┤
│                                         │
│ 📐 数学（45min）                        │
│ ├─ [补] 正比例函数 · 复习巩固（15min）   │
│ │   → 3道变式题                         │
│ ├─ [新] 一次函数概念 · 讲解（20min）     │
│ │   → 互动课件 + 语音讲解               │
│ └─ [练] 一次函数基础题 × 5（10min）      │
│                                         │
│ 🔬 物理（30min）                        │
│ ├─ [补] 速度公式回顾（10min）            │
│ └─ [新] 力的概念 · 讲解+实验（20min）    │
│                                         │
│ 🔤 英语（30min）                        │
│ ├─ 单词打卡 Unit 3（10min）             │
│ └─ 语法：一般过去时 · 讲练（20min）      │
│                                         │
│ ⏱️ 预计总时长：1小时45分                 │
└─────────────────────────────────────────┘
```

**时间分配策略：**

| 阶段 | 时间段 | 数学 | 物理 | 英语 |
|:-----|:-------|:----:|:----:|:----:|
| 暑假（7-8月） | 每天2h | 50% | 30% | 20% |
| 初三上学期 | 每天1.5h | 40% | 30% | 30% |
| 寒假 | 每天2h | 40% | 30% | 30% |
| 初三下/冲刺 | 每天2h | 35% | 35% | 30% |

**学习模式切换：**
- **补课模式**（暑假为主）：回溯初二欠账
- **同步模式**（开学后）：跟学校进度，提前预习+课后巩固
- **冲刺模式**（初三下）：中考真题专项+查漏补缺

---

### 3.4 评估与练习系统

**题库数据结构：**

```json
{
  "id": "math-2024-wuhan-18",
  "node_id": "math-m-linear-function",
  "source": "2024武汉中考第18题",
  "type": "solve",
  "difficulty": 2,
  "question": "已知一次函数y=kx+b经过点(2,3)和(-1,-3)...",
  "answer": "k=2, b=-1, y=2x-1",
  "steps": ["代入(2,3)得2k+b=3", "代入(-1,-3)得-k+b=-3", "联立解得k=2,b=-1"],
  "common_errors": [
    {"error": "符号计算错误", "hint": "代入负数坐标时注意符号"},
    {"error": "解方程组方法错误", "hint": "建议用加减消元法"}
  ],
  "tags": ["中考真题", "代入法", "解方程组"],
  "exam_frequency": 5
}
```

**练习推送策略：**

```
做对了？                          做错了？
  │                                │
  ▼                                ▼
升级难度                        错因分析
同知识点下一级                   ├─ 计算错误 → 再来1道同类
  │                             ├─ 方法不会 → 回到讲解
  ▼                             └─ 前置不牢 → 回溯前置
连续3次对                              │
→ 该点"掌握"                           ▼
→ 进下一个知识点                   加入错题本
                                  3天后再测
```

**评估体系分层：**

| 评估类型 | 触发时机 | 内容 | 时长 |
|:---------|:---------|:-----|:-----|
| 随堂练 | 每个知识点讲完 | 3-5题基础确认 | 5-10min |
| 单元测 | 每章学完 | 该章全部知识点综合 | 30min |
| 月考模拟 | 每月1次 | 已学全部内容 | 90min（数学/物理） |
| 中考模拟 | 初三下每2周 | 全真模拟卷 | 标准考试时长 |

**错题本机制：**
- 自动归集所有错题
- 按知识点聚类
- 遗忘曲线复习：1天/3天/7天/15天后重新推送
- 变式训练：不是重做原题，是同知识点换个数/换个情境

---

### 3.5 语音讲解系统

**技术方案：**

```
知识点讲解文稿（AI生成）
       │
       ▼
  Edge TTS 引擎
  （zh-CN-XiaoxiaoNeural，初中推荐音色）
       │
       ▼
  分段MP3文件（每段对应一个教学环节）
       │
       ▼
  前端播放器 + 课件同步
  （讲到哪里，页面高亮到哪里）
```

**讲解节奏设计（模拟真实老师）：**

```
[引入] "同学们，我们之前学过正比例函数对不对？
       那如果我把这条线往上平移一下，会发生什么？"
       ⟵ 停顿2秒，页面动画演示平移

[讲解] "你看，这条线的方程从 y=2x 变成了 y=2x+1，
       多出来的这个1就是——"
       ⟵ 高亮公式中的 +1

[互动] "现在你来试试，把截距拖到 -2 的位置，
       看看直线怎么变化"
       ⟵ 暂停TTS，等学生操作

[总结] "记住了：k决定斜率（陡不陡），b决定位置（上还是下）"
       ⟵ 关键结论加粗+语音强调
```

**每个知识点的语音教学结构：**
1. **激活旧知**（30秒）— 连接已学内容
2. **制造冲突**（30秒）— 提出问题，激发好奇
3. **核心讲解**（3-5分钟）— 分步骤，配动画
4. **即时检测**（1分钟）— 暂停，让学生做1题
5. **总结口诀**（30秒）— 一句话记住

**英语学科特殊处理：**
- 英语讲解用中文，例句朗读用英文TTS（en-US-JennyNeural）
- 单词发音：英文原声 + 中文释义
- 听力训练：直接用英文TTS生成材料

---

### 3.6 家长看板

**设计原则：** 不需要懂技术，打开就能看懂

```
┌──────────────────────────────────────────────────┐
│ 📊 今日学习报告 · 2026年7月15日                    │
├──────────────────────────────────────────────────┤
│                                                  │
│ ⏱️ 学习时长：1小时52分（目标2小时）✅              │
│                                                  │
│ 📐 数学                                          │
│ ├─ 学了：一次函数概念                             │
│ ├─ 做题：8题，正确6题（75%）                      │
│ └─ 状态：🟡 基本理解，明天继续练                  │
│                                                  │
│ 🔬 物理                                          │
│ ├─ 学了：力的概念                                │
│ ├─ 做题：5题，正确4题（80%）                      │
│ └─ 状态：🟢 掌握良好                             │
│                                                  │
│ 🔤 英语                                          │
│ ├─ 单词：打卡15个，记住12个                       │
│ ├─ 语法：一般过去时练习 正确率70%                 │
│ └─ 状态：🟡 过去时不规则变化需加强                │
│                                                  │
│ 📈 本周趋势：数学↑12% 物理↑8% 英语→持平          │
│                                                  │
│ ⚠️ 需关注：                                      │
│ · 数学"解方程组"连续2天正确率低于60%              │
│ · 英语单词遗忘率偏高，建议增加复习频次            │
└──────────────────────────────────────────────────┘
```

**数据维度：**
- 每日：时长、题量、正确率、知识点进度
- 每周：趋势图（各科掌握度变化曲线）
- 每月：模拟考成绩、对比上月、预估中考分数段

---

### 3.7 趣味性设计

| 机制 | 实现方式 |
|:-----|:---------|
| 经验值/等级 | 做题得经验，升级解锁新称号 |
| 连续打卡 | 日历显示学习天数，断了会心疼 |
| 成就徽章 | "一次函数大师""力学新手"等里程碑 |
| 物理虚拟实验 | Canvas/PhET模拟：浮力、电路、光路 |
| 数学动态图 | 函数图像实时变化、几何拖拽证明 |
| 每日挑战 | 1道趣味题（非考试题），答对奖励双倍经验 |
| 进度地图 | 类似游戏关卡地图，清晰看到走到哪了 |

**不做的：** 排行榜（只有1个人没意义）、社交功能、过度游戏化（喧宾夺主）

---

## 四、TeachAny 复用策略

| TeachAny 能力 | 复用方式 | 改造点 |
|:--------------|:---------|:-------|
| 互动课件模板 | ✅ 直接用 | 改为初中视觉模式 |
| TTS引擎(Edge Neural) | ✅ 直接用 | 用其脚本生成MP3 |
| 知识树(node_id体系) | ✅ 直接用 | 补充武汉中考权重 |
| 五镜头教学法 | ✅ 直接用 | 生成课件时遵循 |
| ABT叙事结构 | ✅ 直接用 | 每课开头设计 |
| 三级脚手架练习 | ✅ 直接用 | 对应基础/提高/挑战 |
| 错因诊断框架 | ✅ 直接用 | 扩展到题库系统 |
| AI学伴模块 | ⚠️ 改造 | 接入自己的LLM API |
| Gallery/发布系统 | ❌ 不用 | 单用户不需要 |
| 社区/评审流程 | ❌ 不用 | 自己的系统 |
| 地图/历史课件 | ❌ 不用 | 不教地理历史 |

**课件生成流程（复用TeachAny Skill）：**

```bash
# 1. 用TeachAny生成互动教学课件
# 输入：知识点 + 年级 + 前置知识
# 输出：单文件HTML（含Canvas互动+TTS+练习）

# 2. 后端API调用AI生成课件脚本
POST /api/courseware/generate
{
  "node_id": "math-m-linear-function",
  "grade": 8,
  "student_mastery": { "proportional-function": 0.7 },
  "style": "middle-school"
}

# 3. 生成的HTML课件存入 /courseware/<node_id>/index.html
# 4. 学生访问时从后端获取该课件URL
```

---

## 五、数据模型

### 5.1 核心表结构（SQLite）

```sql
-- 知识点图谱
CREATE TABLE knowledge_nodes (
    node_id TEXT PRIMARY KEY,           -- math-m-linear-function
    subject TEXT NOT NULL,              -- math/physics/english
    name TEXT NOT NULL,                 -- 一次函数
    grade INTEGER,                     -- 8
    semester INTEGER,                  -- 1=上学期 2=下学期
    chapter TEXT,                      -- 人教版八上·第11章
    prerequisites TEXT,                -- JSON: ["node-a","node-b"]
    exam_weight TEXT,                  -- high/medium/low
    exam_points TEXT,                  -- "10-12"
    estimated_minutes INTEGER,         -- 预计学习时长
    courseware_path TEXT                -- 课件HTML路径
);

-- 学情记录（每次做题产生一条）
CREATE TABLE mastery_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    question_id TEXT,
    correct INTEGER,                   -- 1=对 0=错
    time_spent_sec INTEGER,            -- 做题用时
    error_type TEXT,                   -- 错因分类
    FOREIGN KEY (node_id) REFERENCES knowledge_nodes(node_id)
);

-- 知识点掌握度（计算后的快照）
CREATE TABLE mastery_summary (
    node_id TEXT PRIMARY KEY,
    mastery REAL DEFAULT 0,            -- 0.0 ~ 1.0
    status TEXT DEFAULT 'not_started', -- not_started/learning/mastered
    last_practice TEXT,                -- 最后练习时间
    total_attempts INTEGER DEFAULT 0,
    correct_rate REAL DEFAULT 0,
    next_review TEXT,                  -- 下次复习时间（遗忘曲线）
    FOREIGN KEY (node_id) REFERENCES knowledge_nodes(node_id)
);

-- 题库
CREATE TABLE questions (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    source TEXT,                        -- "2024武汉中考第18题"
    type TEXT,                          -- choice/fill/solve/proof
    difficulty INTEGER,                 -- 1-3
    question TEXT NOT NULL,             -- 题干（支持LaTeX）
    options TEXT,                       -- JSON，选择题用
    answer TEXT NOT NULL,
    steps TEXT,                         -- JSON: 解题步骤
    common_errors TEXT,                 -- JSON: 常见错误
    tags TEXT,                          -- JSON: 标签
    exam_frequency INTEGER DEFAULT 0,
    FOREIGN KEY (node_id) REFERENCES knowledge_nodes(node_id)
);

-- 错题本
CREATE TABLE error_book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    first_error_time TEXT,
    error_count INTEGER DEFAULT 1,
    error_type TEXT,
    review_stage INTEGER DEFAULT 0,    -- 0=新错 1=1天后 2=3天后 3=7天后 4=已掌握
    next_review TEXT,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- 每日学习计划
CREATE TABLE daily_plans (
    date TEXT PRIMARY KEY,              -- 2026-07-15
    plan TEXT NOT NULL,                 -- JSON: 当天计划详情
    actual TEXT,                        -- JSON: 实际完成情况
    total_minutes INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0         -- 1=已完成
);

-- 学习统计（家长看板用）
CREATE TABLE daily_stats (
    date TEXT PRIMARY KEY,
    math_minutes INTEGER DEFAULT 0,
    physics_minutes INTEGER DEFAULT 0,
    english_minutes INTEGER DEFAULT 0,
    math_correct_rate REAL,
    physics_correct_rate REAL,
    english_correct_rate REAL,
    questions_total INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    nodes_learned TEXT                  -- JSON: 当天学习的知识点列表
);
```

### 5.2 知识图谱数据（JSON文件）

```
data/
├── math/
│   ├── tree.json              # 数学知识树（含依赖关系）
│   ├── grade8-semester1.json  # 八上知识点列表
│   ├── grade8-semester2.json  # 八下
│   └── grade9.json            # 九年级
├── physics/
│   ├── tree.json
│   ├── grade8-semester1.json
│   ├── grade8-semester2.json
│   └── grade9.json
├── english/
│   ├── tree.json
│   ├── grade8-units.json
│   └── grade9-units.json
└── exam/
    ├── wuhan-math-2019-2025.json   # 武汉中考数学真题
    ├── wuhan-physics-2019-2025.json
    └── wuhan-english-2019-2025.json
```

---

## 六、开发路线图
### Phase 1 · MVP（已完成）— 能用

> 平台骨架 + 数学诊断/练习/错题本

- [x] 搭建FastAPI + Vue3项目骨架
- [x] Docker Compose + Nginx（nginx改8088供cloudflared回源）
- [x] 数学知识树（已对齐 TeachAny 官方50节点）
- [x] 入学诊断卷 + 实时掌握度 + 前置回溯
- [x] 智能做题（答题+判分+错因提示）+ 错题本（遗忘曲线）
- [x] 简版每日计划自动生成
- [x] 本地端到端验证通过

### Phase 2 · 全科骨架 + 知识地图（进行中）— 形态成型

> 目标：全科数据进库，知识地图/全科图谱可视化，打通第一个课件

- [x] 数学树对齐 TeachAny 官方 node_id + prerequisites + 课标点
- [ ] 导入初中全科 10 科官方树（语数英物化生地史道法心理）
- [ ] 后端全科节点/图谱 API（多学科、依赖图、掌握度叠加）
- [ ] 知识地图视图（单学科节点图 + 依赖连线 + 掌握度色）
- [ ] 全科图谱视图（跨学科总览）
- [ ] 打通第一个课件全链路（teachany 课件 → 自托管 → Learn 页 → 验证互动/TTS/AI学伴）
- [ ] 修家长看板 daily_stats 写入

**Phase 2 交付物：** 全科知识地图成型 + 课件主线验证 + 可上线给孩子用

### Phase 3 · 课件库 + 学习路径 — 好用

> 目标：课件可浏览、个性化学习路径

- [ ] 课件库浏览视图（本系统形式）
- [ ] 批量拉取/生成高频知识点课件（先数理英）
- [ ] 学习路径（path）个性化生成与可视化
- [ ] 掌握度算法增强 + 自动推题
- [ ] 家长看板：周趋势图、薄弱点提醒

### Phase 4 · PBL + 阅读学院 — 全形态

> 目标：补齐 teachany.cn 形态的探究与阅读模块

- [ ] PBL 探究路径模块（集成 teachany.cn PBL 或自建）
- [ ] 阅读学院模块（语文阅读专题）
- [ ] 经验值/成就系统
- [ ] 单元测试 + 模拟考

### Phase 5 · 初三准备 + 冲刺

> 目标：初三内容、中考专项

- [ ] 初三全科课件批量生成
- [ ] "同步模式"（跟学校进度）
- [ ] 中考真题专项 + 全真模拟 + 考频分析
- [ ] 中考倒计时 + 分数预估

---

## 六·B、内容生产流水线（课件 / 教材 / 试卷）

| 内容 | 角色 | 处理方式 |
|:---|:---|:---|
| **课件** | 教学核心 | 已有→teachany.cn取静态文件自托管；缺→TeachAny Skill完整模式生成。"课件缺口报告"自动按"学校进度×掌握度×考频×覆盖"排优先级 |
| **教材**（人教版·武汉） | 内容源+对齐基准 | 提取章节结构校准树/进度；索引到知识库供课件生成参照；官方树已带 textbook_chapter + curriculum_points |
| **本地试卷**（武汉真题/模拟） | 题库源+考频校准 | OCR/LLM提取→题库JSON→标 node_id→导入；校准 exam_weight；支撑模拟考。带图题单独挂附件 |

---

## 七、目录结构规划

```
teachany/                          # 项目根目录
├── docker-compose.yml             # 一键部署
├── nginx.conf                     # 反代配置
├── backend/                       # Python FastAPI
│   ├── main.py                    # 入口
│   ├── api/
│   │   ├── diagnosis.py           # 诊断接口
│   │   ├── study_plan.py          # 学习计划
│   │   ├── questions.py           # 题库/做题
│   │   ├── graph.py               # 知识地图/全科图谱/路径 API（新增）
│   │   ├── courseware.py          # 课件库/课件管理（新增）
│   │   ├── pbl.py                 # PBL 探究（新增）
│   │   ├── reading.py             # 阅读学院（新增）
│   │   ├── stats.py              # 统计/报告
│   │   └── tts.py                # TTS生成
│   ├── core/
│   │   ├── mastery.py            # 掌握度计算
│   │   ├── path_engine.py        # 学习路径引擎
│   │   ├── question_selector.py  # 智能选题
│   │   └── review_scheduler.py   # 复习调度（遗忘曲线）
│   ├── db/
│   │   ├── schema.sql
│   │   └── database.py
│   └── requirements.txt
├── frontend/                      # Vue 3
│   ├── src/
│   │   ├── views/
│   │   │   ├── StudentHome.vue    # 学生主页（今日计划）
│   │   │   ├── KnowledgeMap.vue   # 知识地图（单学科，新增）
│   │   │   ├── SubjectGraph.vue   # 全科图谱（新增）
│   │   │   ├── LearningPath.vue   # 学习路径（新增）
│   │   │   ├── CoursewareLib.vue  # 课件库（新增）
│   │   │   ├── PBL.vue            # PBL探究（新增）
│   │   │   ├── Reading.vue        # 阅读学院（新增）
│   │   │   ├── Learn.vue          # 课件学习页
│   │   │   ├── Practice.vue       # 做题页
│   │   │   ├── ErrorBook.vue      # 错题本
│   │   │   ├── Diagnosis.vue      # 诊断测试
│   │   │   ├── Progress.vue       # 进度地图
│   │   │   └── ParentDash.vue     # 家长看板
│   │   └── components/
│   ├── package.json
│   └── vite.config.ts
├── courseware/                     # TeachAny生成的课件
│   ├── math/
│   │   ├── linear-function/
│   │   │   ├── index.html         # 互动教学页
│   │   │   └── tts/               # 语音文件
│   │   └── ...
│   ├── physics/
│   └── english/
├── data/                          # 知识图谱+题库
│   ├── math/
│   ├── physics/
│   ├── english/
│   └── exam/
├── tools/                         # 辅助工具
│   ├── import_questions.py        # 导入真题
│   ├── generate_courseware.py     # 批量生成课件
│   └── tts_batch.py              # 批量生成语音
└── TECHNICAL_PLAN.md              # 本文件
```

---

## 八、部署方案

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./courseware:/app/courseware
      - ./db:/app/db

  frontend:
    build: ./frontend
    ports:
      - "3000:80"

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./courseware:/var/www/courseware  # 静态课件直出
      - ./certs:/etc/nginx/certs
    depends_on:
      - backend
      - frontend
```

**访问方式：**
- 学生：`https://your-domain/` → 学习主界面
- 家长：`https://your-domain/parent` → 看板（可加简单密码）
- 课件：`https://your-domain/courseware/math/linear-function/` → 直出HTML

**服务器要求：**
- 最低：1核2G（轻量云服务器/家里闲置电脑均可）
- 存储：10G起步（课件+音频会逐渐增长）
- 带宽：家用宽带的上行就够（1人用）

---

## 九、关键决策点（需你确认）

1. **AI学伴** — 用云端API（OpenAI/智谱/通义，有成本但质量好）还是本地Ollama（免费但需GPU/效果一般）？

2. **课件生成方式** — 前期手动用AI助手逐个生成（质量高但慢），还是写脚本批量生成（快但可能需要人工校对）？

3. **英语听力/口语** — 只做阅读+语法+写作训练，还是也要做听力材料？口语练习需要吗？

4. **服务器** — 用家里电脑（免费、但要长期开机），还是买轻量云服务器（阿里云/腾讯云，约50-100元/月）？

5. **数学公式渲染** — 用KaTeX（快、轻量）还是MathJax（全面、稍重）？

6. **暑假开始时间** — 什么时候需要MVP可用？是现在就开始做，还是有个时间窗口？

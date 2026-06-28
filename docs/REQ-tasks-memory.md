# 需求文档：家长任务系统 + 艾宾浩斯记忆系统

> 版本：v1.0 · 2026-06-28
> 状态：待确认

---

## 一、家长任务布置与监控系统

### 1.1 概述

家长可以在家长端（`/parent`）给学生布置学习任务，学生在首页看到"今日任务"，完成后家长可看到执行情况（完成率、正确率、用时）。

### 1.2 任务类型

| 类型 | 示例 | 完成判定 |
|------|------|---------|
| 做题 | "完成一次函数10道练习" | 提交答题记录 ≥ 指定题量 |
| 看课件 | "学习全等三角形课件" | 打开课件页面并停留 ≥ 3分钟 |
| 背诵 | "背诵Unit3单词30个" | 完成记忆系统当日复习量 |
| 自定义 | "做一套数学模拟卷并对答案" | 学生手动打卡标记完成 |

### 1.3 任务属性

```
{
  "title": "任务标题",
  "type": "practice | courseware | memory | custom",
  "subject": "math",              // 可选，关联学科
  "node_id": "math-m-xxx",        // 可选，关联知识点
  "target_count": 10,             // 做题类：目标题数
  "deadline": "2026-06-29",       // 截止日期
  "repeat": null | {              // 循环设置
    "frequency": "daily | weekly",
    "end_date": "2026-07-15"      // 循环结束日期，null为永久
  },
  "note": "家长备注"
}
```

### 1.4 页面设计

**家长端（`/parent` 页面新增区域）：**
- 「布置任务」按钮 → 弹出表单（类型/学科/知识点/题量/截止时间/循环/备注）
- 「任务列表」：当前活跃任务 + 历史任务
- 每个任务显示：完成状态（✅/⏳/❌过期）、完成时间、正确率（做题类）

**学生首页（`/` 顶部新增）：**
- 「今日任务」卡片区：未完成的任务列表
- 每个任务可点击跳转到对应页面（练习/课件/记忆/打卡）
- 完成后显示 ✅ 状态

### 1.5 数据模型

```sql
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  type TEXT NOT NULL,            -- practice/courseware/memory/custom
  subject TEXT,
  node_id TEXT,
  target_count INTEGER DEFAULT 0,
  deadline TEXT NOT NULL,         -- YYYY-MM-DD
  repeat_frequency TEXT,          -- null/daily/weekly
  repeat_end TEXT,                -- 循环结束日期
  note TEXT,
  status TEXT DEFAULT 'active',   -- active/completed/expired
  created_at TEXT DEFAULT (datetime('now','localtime')),
  completed_at TEXT,
  result_data TEXT                -- JSON: {correct_rate, time_spent, ...}
);
```

### 1.6 API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/tasks/list | 家长看全部任务（可按状态筛选） |
| POST | /api/tasks/create | 家长布置任务 |
| PUT | /api/tasks/{id} | 修改任务 |
| DELETE | /api/tasks/{id} | 删除任务 |
| GET | /api/tasks/today | 学生获取今日待完成任务 |
| POST | /api/tasks/{id}/complete | 学生标记完成（或系统自动判定） |

---

## 二、艾宾浩斯记忆系统

### 2.1 概述

基于遗忘曲线的科学记忆工具，适用于需要大量重复背诵的学科内容。系统自动调度复习时间，学生每天完成推送的复习量。

### 2.2 适用学科与内容

| 学科 | 记忆内容 | 卡片格式 |
|------|---------|---------|
| 英语 | 单词表、语法规则、阅读高频词汇、句型 | 正面：英文/用法 → 背面：中文释义/例句 |
| 历史 | 考点（事件/时间/人物/意义） | 正面：问题 → 背面：答案要点 |
| 道法 | 考点（法律条文/核心观点/案例分析） | 正面：问题 → 背面：答案要点 |
| 语文 | 古诗文默写、文言文字词 | 正面：上句/字词 → 背面：下句/释义 |

### 2.3 记忆算法

**复习阶段（艾宾浩斯间隔）：**

```
阶段0: 新卡片（当天学习）
阶段1: 1天后复习
阶段2: 3天后复习
阶段3: 7天后复习
阶段4: 15天后复习
阶段5: 30天后复习
阶段6: 永久记住（不再推送）
```

**升降级规则：**
- 回忆正确 → 升一级（下次复习间隔拉长）
- 回忆错误 → 降回阶段1（重新开始间隔）
- 连续正确3次跳级（加速掌握的内容）

### 2.4 记忆模式

| 模式 | 交互方式 | 适用 |
|------|---------|------|
| **翻卡模式** | 看正面→心中回忆→翻看背面→自评对错 | 所有学科 |
| **拼写模式** | 看中文释义→输入英文拼写→判定 | 英语单词 |
| **听写模式**（可选） | 播放单词发音→输入拼写→判定 | 英语单词 |

学生可切换模式。默认翻卡模式，英语自动启用拼写模式。

### 2.5 每日推送逻辑

```
每日复习量 = 到期复习卡片 + 新学卡片

到期复习: 按review_date <= today筛选，按阶段低→高排序
新学卡片: 系统默认每天新增20张（家长可在任务中调整为10-50）
```

**家长控制：**
- 可通过任务系统布置"今天背30个单词"（覆盖系统默认的20张）
- 可暂停某学科的记忆推送
- 可查看记忆进度（总卡片数/已掌握/学习中/待学）

### 2.6 数据模型

```sql
-- 记忆卡片库
CREATE TABLE memory_cards (
  id INTEGER PRIMARY KEY,
  subject TEXT NOT NULL,          -- english/history/politics/chinese
  category TEXT,                  -- vocab/grammar/reading_words/poem/facts
  front TEXT NOT NULL,            -- 正面（问题/单词）
  back TEXT NOT NULL,             -- 背面（答案/释义）
  audio_url TEXT,                 -- 可选：发音音频
  source TEXT,                    -- 来源（教材/考点/AI生成）
  difficulty INTEGER DEFAULT 1    -- 1-3
);

-- 学生记忆进度
CREATE TABLE memory_progress (
  id INTEGER PRIMARY KEY,
  card_id INTEGER NOT NULL,
  stage INTEGER DEFAULT 0,        -- 0-6 复习阶段
  review_date TEXT NOT NULL,      -- 下次复习日期 YYYY-MM-DD
  correct_streak INTEGER DEFAULT 0, -- 连续正确次数
  total_reviews INTEGER DEFAULT 0,
  total_correct INTEGER DEFAULT 0,
  last_reviewed TEXT,
  FOREIGN KEY (card_id) REFERENCES memory_cards(id)
);
```

### 2.7 页面设计

**记忆训练页（新路由 `/memory`）：**
- 顶部：今日进度条（已复习/总量）
- 学科 tab 切换
- 卡片区：
  - 翻卡模式：正面显示 → 点击翻转 → 自评"记住了"/"没记住"
  - 拼写模式：显示中文 → 输入框 → 提交判定
- 底部：剩余数量、正确率统计

**导航：** 主导航加"记忆"入口（📇 记忆）

### 2.8 API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/memory/today | 获取今日复习队列（到期+新卡） |
| POST | /api/memory/review | 提交复习结果（card_id + correct） |
| GET | /api/memory/stats | 记忆进度统计（各阶段分布） |
| GET | /api/memory/cards/{subject} | 浏览卡片库 |
| POST | /api/memory/settings | 家长设置每日新卡数量 |

### 2.9 卡片数据生产

| 来源 | 方式 | 预计量 |
|------|------|--------|
| 英语教材 | 从 PDF 提取单词表 + AI 生成例句 | ~2000张 |
| 英语语法/阅读 | AI 按语法点/阅读策略生成 | ~300张 |
| 历史考点 | AI 从知识树节点生成问答卡片 | ~500张 |
| 道法考点 | AI 从知识树节点生成问答卡片 | ~300张 |
| 语文古诗文 | AI 从教材提取默写填空卡片 | ~200张 |

总计约 **3300 张记忆卡片**，可后续持续扩充。

---

## 三、实施计划

| 阶段 | 内容 | 预计时间 |
|------|------|---------|
| 1 | 任务系统（后端+家长端+学生首页） | 2小时 |
| 2 | 记忆系统核心（表结构+算法+API+前端训练页） | 3小时 |
| 3 | 记忆卡片数据生产（AI批量生成3300张） | 2-3小时（后台跑） |
| 4 | 联调：任务系统关联记忆系统（布置背诵任务→关联每日量） | 1小时 |

---

## 四、已确认

1. ✅ 听写模式需要 TTS 音频（用 Edge TTS 免费生成）
2. ✅ 任务过期未完成：家长端+学生端都标红提示
3. ✅ 记忆卡片不需要家长手动添加/编辑（全部系统生成）

---

请确认是否可以开始实施，或有需要修改的地方。

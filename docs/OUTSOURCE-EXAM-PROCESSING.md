# 试卷 & 教材处理 — 外包交付说明

> 负责人：Marvis
> 仓库：github.com/zjianchun/LearnAnything
> 分支：直接提交到 `main`

---

## 一、任务概述

将 `data/exams/` 和 `data/textbook/` 中的 PDF 文件处理为结构化 JSON 题库 + 页面截图，供练习系统使用。

**规模：**
- 试卷：441 份 PDF（已过滤解析版后约 350 份有效）
- 教材：34 份 PDF

**注意：数学科目已在处理中（约110份），请跳过或处理完后合并去重。**

---

## 二、输入文件位置

```
data/exams/中考试卷/
├── 中考数学/       ← 约110份 (已在处理,可跳过)
├── 中考物理/       ← 约74份
├── 中考化学/       ← 约44份
├── 中考英语/       ← 约34份
├── 中考语文/       ← 约42份
├── 中考历史/       ← 约23份
├── 中考道法/       ← 约24份
└── ...

data/textbook/       ← 34份教材PDF
```

**跳过条件：** 文件名含"解析""答案版""解答"的 PDF 不处理（纯答案没有题目）。

---

## 三、输出格式

### 3.1 JSON 文件

每科一个文件，路径：`data/<subject>/exam-questions-v2.json`

```json
[
  {
    "question_num": "1",
    "question": "已知 $\\triangle ABC$ 中，$\\angle C=90°$，$AC=3$，$BC=4$，求 $AB$ 的长。",
    "answer": "5",
    "type": "short_answer",
    "difficulty": 1,
    "node_keywords": ["勾股定理", "直角三角形"],
    "exam_frequency": 5,
    "figure_description": "直角三角形ABC，∠C=90°，AC=3，BC=4，求斜边AB",
    "figure_url": "/exam-pages/math/a1b2c3d4.webp",
    "source_pdf": "数学_真题_2025_武汉中考数学.pdf",
    "source_page": 2
  }
]
```

### 3.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question_num | string | ✅ | 原始题号 |
| question | string | ✅ | 完整题目文本，**公式用 LaTeX**（`$...$`） |
| answer | string/null | ❌ | 正确答案，没有填 `null` |
| type | string | ✅ | `choice` / `fill` / `short_answer` / `proof` / `experiment` / `reading` |
| difficulty | int | ✅ | 1=基础 2=中等 3=拔高 |
| node_keywords | array | ✅ | 2-4个知识点关键词 |
| exam_frequency | int | ✅ | 3=普通 4=常考 5=必考 |
| figure_description | string/null | ✅ | 有图→精确描述几何关系/表格数据；无图→`null` |
| figure_url | string | ❌ | 有图时填，格式 `/exam-pages/<subject>/<filename>.webp` |
| source_pdf | string | ✅ | 来源 PDF 文件名 |
| source_page | int | ✅ | 来源页码（从0开始） |

### 3.3 图片文件

路径：`data/exam-pages/<subject>/<filename>.webp`

- **只有题目含图形/表格/实验图时才保存**（纯文字题不需要图片）
- 格式：WebP，quality 80
- 分辨率：150 DPI 渲染 PDF 页面
- 文件名：随意（hash/序号均可），与 JSON 中 `figure_url` 对应

### 3.4 学科目录名对照

| 中文 | 目录名 |
|------|--------|
| 数学 | `math` |
| 物理 | `physics` |
| 化学 | `chemistry` |
| 英语 | `english` |
| 语文 | `chinese` |
| 生物 | `biology` |
| 历史 | `history` |
| 道法/政治 | `politics` |
| 地理 | `geography` |

---

## 四、质量要求

### 4.1 公式

- 所有数学/物理/化学公式必须用 LaTeX：`$x^2 + 2x - 3 = 0$`
- 常用符号：`$\triangle$` `$\angle$` `$\perp$` `$\parallel$` `$\frac{a}{b}$` `$\sqrt{3}$` `$\overrightarrow{AB}$`
- 不要用 Unicode 特殊字符替代

### 4.2 图形描述

当题目有图时，`figure_description` 必须足够详细，使得不看图也能做题：

```
✅ 好："直角三角形ABC，∠C=90°，D为AB中点，E为AC上一点使DE⊥AB，BC=6，AC=8"
❌ 差："如图所示的三角形"
```

### 4.3 去重

- 同一题在"原卷版"和"考试版"可能重复出现，按 `question` 文本相似度去重
- 同一 PDF 如果有多个版本（`_2.pdf` `_3.pdf`），通常内容相同，处理一份即可

### 4.4 选择题格式

选项写在 `question` 字段内：

```
"question": "下列各式中，计算正确的是（）\nA. $a^2 \\cdot a^3 = a^6$\nB. $(a^2)^3 = a^6$\nC. $a^6 ÷ a^2 = a^3$\nD. $(ab)^2 = ab^2$"
```

---

## 五、现成工具

仓库里有一个可以直接用的处理脚本：

```bash
# 安装依赖
pip install pymupdf httpx pillow python-dotenv

# 配置 API Key（在 .env 文件中）
MINIMAX_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.minimax.chat/v1

# 运行（按学科）
python tools/process_exams_v2.py --subject 物理
python tools/process_exams_v2.py --subject 化学
python tools/process_exams_v2.py --subject 英语

# 支持断点续传
python tools/process_exams_v2.py --subject 物理 --resume

# 跳过前N份
python tools/process_exams_v2.py --subject 物理 --skip 30

# 限制处理数量（测试用）
python tools/process_exams_v2.py --subject 物理 --limit 5
```

**也可以用其他模型/工具处理**（GPT-4o、Gemini 等），只要输出格式一致即可。

### 速度参考

- MiniMax M3：约 30 秒/页，一份 8 页试卷约 4-5 分钟
- 全量约 3400 页，单线程约 67 小时
- 建议按学科并行开多个进程

---

## 六、提交方式

直接 commit 到 `main` 分支：

```bash
git add data/<subject>/exam-questions-v2.json
git add data/exam-pages/<subject>/
git commit -m "data: <学科>试卷提取 - XX份PDF, XX道题"
git push origin main
```

**建议每完成一科就提交一次**，不要攒到最后。

---

## 七、验证

提交后可以在本地验证 JSON 格式：

```python
import json
data = json.loads(open("data/physics/exam-questions-v2.json").read())
print(f"共 {len(data)} 题")
# 检查必填字段
for q in data:
    assert q.get("question"), f"缺少question: {q}"
    assert q.get("type") in ("choice","fill","short_answer","proof","experiment","reading")
    assert q.get("difficulty") in (1,2,3)
    assert isinstance(q.get("node_keywords"), list) and len(q["node_keywords"]) >= 1
```

---

## 八、优先级

1. **物理**（图多，最需要多模态处理）
2. **化学**（实验图多）
3. **英语**
4. **语文**
5. **历史/道法**（文字为主，相对简单）

数学已在处理中，不需要做。

---

## 九、联系

有格式问题直接在仓库提 issue 或联系我。

"""为exam-questions-v2.json中的真题匹配node_id，生成可被seed.py加载的格式"""
import json, hashlib
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# 关键词 → node_id 映射（按学科）
KEYWORD_MAP = {
    "math": {
        "有理数": "math-m-rational-number",
        "数轴": "math-m-real-number",
        "实数": "math-m-real-number",
        "代数式": "math-m-algebraic-expression",
        "整式": "math-m-algebraic-expressions",
        "整式加减": "math-m-algebraic-expressions",
        "因式分解": "math-m-monomial-multiplication",
        "整式乘除": "math-m-monomial-multiplication",
        "一元一次方程": "math-m-linear-equation-one",
        "二元一次方程": "math-m-linear-equation-two",
        "方程组": "math-m-linear-equation-two",
        "不等式": "math-m-inequalities",
        "一元一次不等式": "math-m-linear-inequality",
        "分式": "math-m-fraction-expression",
        "分式方程": "math-m-fraction-equation",
        "二次根式": "math-m-quadratic-radical",
        "一元二次方程": "math-m-quadratic-equation",
        "坐标": "math-m-coordinate-system",
        "直角坐标": "math-m-coordinate-system",
        "一次函数": "math-m-linear-function",
        "正比例函数": "math-m-proportional-function",
        "反比例函数": "math-m-inverse-proportion",
        "二次函数": "math-m-quadratic-function",
        "抛物线": "math-m-quadratic-function",
        "函数": "math-m-variable-and-function",
        "相交线": "math-m-line-angle",
        "平行线": "math-m-line-angle",
        "三角形": "math-m-triangle-basics",
        "全等三角形": "math-m-geometry-congruent-triangles",
        "全等": "math-m-geometry-congruent-triangles",
        "等腰三角形": "math-m-isosceles-triangle",
        "等边三角形": "math-m-isosceles-triangle",
        "相似三角形": "math-m-similar-triangles",
        "相似": "math-m-similar-triangles",
        "勾股定理": "math-m-pythagorean-theorem",
        "勾股": "math-m-pythagorean-theorem",
        "四边形": "math-m-quadrilateral",
        "平行四边形": "math-m-special-quadrilateral",
        "矩形": "math-m-special-quadrilateral",
        "菱形": "math-m-special-quadrilateral",
        "正方形": "math-m-special-quadrilateral",
        "梯形": "math-m-special-quadrilateral",
        "轴对称": "math-m-axial-symmetry",
        "旋转": "math-m-rotation",
        "平移": "math-m-translation-dilation",
        "位似": "math-m-translation-dilation",
        "圆": "math-m-circle-basics",
        "圆心角": "math-m-circle-angle",
        "圆周角": "math-m-circle-angle",
        "切线": "math-m-circle-tangent",
        "弧长": "math-m-arc-sector",
        "扇形": "math-m-arc-sector",
        "内切圆": "math-m-inscribed-circumscribed",
        "外接圆": "math-m-inscribed-circumscribed",
        "三角函数": "math-m-trig-ratio",
        "锐角三角函数": "math-m-trig-ratio",
        "正弦": "math-m-trig-ratio",
        "余弦": "math-m-trig-ratio",
        "正切": "math-m-trig-ratio",
        "概率": "math-m-probability-basic",
        "频率": "math-m-probability-frequency",
        "统计": "math-m-statistics-probability-junior",
        "数据分析": "math-m-data-analysis",
        "均值": "math-m-data-analysis",
        "中位数": "math-m-data-analysis",
        "方差": "math-m-data-analysis",
        "抽样": "math-m-sampling-estimation",
        "尺规作图": "math-m-ruler-compass-construction",
    },
    "physics": {
        "声": "physics-m-sound",
        "声音": "physics-m-sound",
        "光": "physics-m-light-basics",
        "反射": "physics-m-light-reflection",
        "折射": "physics-m-light-refraction",
        "凸透镜": "physics-m-convex-lens",
        "透镜": "physics-m-convex-lens",
        "温度": "physics-m-temperature",
        "物态变化": "physics-m-phase-change",
        "熔化": "physics-m-phase-change",
        "汽化": "physics-m-phase-change",
        "质量": "physics-m-mass-density",
        "密度": "physics-m-mass-density",
        "力": "physics-m-force",
        "重力": "physics-m-gravity",
        "弹力": "physics-m-force",
        "摩擦力": "physics-m-friction",
        "压强": "physics-m-pressure",
        "液体压强": "physics-m-liquid-pressure",
        "大气压": "physics-m-atmospheric-pressure",
        "浮力": "physics-m-buoyancy",
        "杠杆": "physics-m-lever",
        "滑轮": "physics-m-pulley",
        "功": "physics-m-work-power",
        "功率": "physics-m-work-power",
        "机械效率": "physics-m-mechanical-efficiency",
        "动能": "physics-m-kinetic-energy",
        "势能": "physics-m-potential-energy",
        "内能": "physics-m-internal-energy",
        "热量": "physics-m-heat-transfer",
        "比热容": "physics-m-specific-heat",
        "电路": "physics-m-circuit-basics",
        "电流": "physics-m-current",
        "电压": "physics-m-voltage",
        "电阻": "physics-m-resistance",
        "欧姆定律": "physics-m-ohms-law",
        "电功": "physics-m-electric-power",
        "电功率": "physics-m-electric-power",
        "电磁": "physics-m-electromagnetism",
        "磁": "physics-m-magnetism",
        "运动": "physics-m-motion",
        "速度": "physics-m-speed",
        "惯性": "physics-m-inertia-newton",
        "牛顿": "physics-m-inertia-newton",
    },
    "chemistry": {
        "空气": "chemistry-m-air-composition",
        "氧气": "chemistry-m-oxygen",
        "制取氧气": "chemistry-m-oxygen",
        "水": "chemistry-m-water",
        "分子": "chemistry-m-molecule-atom",
        "原子": "chemistry-m-molecule-atom",
        "元素": "chemistry-m-elements",
        "化学式": "chemistry-m-chemical-formula",
        "化合价": "chemistry-m-chemical-formula",
        "质量守恒": "chemistry-m-conservation-mass",
        "化学方程式": "chemistry-m-chemical-equation",
        "碳": "chemistry-m-carbon",
        "一氧化碳": "chemistry-m-carbon-oxide",
        "二氧化碳": "chemistry-m-carbon-oxide",
        "金属": "chemistry-m-metals",
        "金属活动性": "chemistry-m-metal-activity",
        "溶液": "chemistry-m-solution",
        "溶解度": "chemistry-m-solubility",
        "酸": "chemistry-m-acid-base",
        "碱": "chemistry-m-acid-base",
        "盐": "chemistry-m-salt",
        "中和": "chemistry-m-neutralization",
        "化肥": "chemistry-m-fertilizer",
        "燃烧": "chemistry-m-combustion",
    },
    "english": {
        "词汇": "english-m-vocabulary-core",
        "语法": "english-m-grammar-tenses",
        "时态": "english-m-grammar-tenses",
        "阅读": "english-m-reading-comprehension",
        "完形填空": "english-m-cloze",
        "写作": "english-m-writing",
        "听力": "english-m-listening",
    },
}


def match_node_id(subject: str, keywords: list) -> str:
    """根据关键词列表匹配最佳node_id"""
    kw_map = KEYWORD_MAP.get(subject, {})
    for kw in keywords:
        if kw in kw_map:
            return kw_map[kw]
    # 模糊匹配：关键词包含映射中的key
    for kw in keywords:
        for map_kw, node_id in kw_map.items():
            if map_kw in kw or kw in map_kw:
                return node_id
    return ""


def process_subject(subject: str):
    """处理一个学科的真题，添加node_id和id字段"""
    exam_file = DATA_DIR / subject / "exam-questions-v2.json"
    if not exam_file.exists():
        return []

    questions = json.loads(exam_file.read_text())
    result = []
    matched = 0

    for i, q in enumerate(questions):
        keywords = q.get("node_keywords", [])
        node_id = match_node_id(subject, keywords)
        if not node_id:
            continue

        # 生成唯一ID
        qid = f"{subject}-exam-{hashlib.md5((q.get('question','')[:50] + str(i)).encode()).hexdigest()[:8]}"

        result.append({
            "id": qid,
            "node_id": node_id,
            "source": q.get("source_pdf", "真题"),
            "type": q.get("type", "choice"),
            "difficulty": q.get("difficulty", 2),
            "question": q.get("question", ""),
            "options": q.get("options", []) if isinstance(q.get("options"), list) else [],
            "answer": q.get("answer", ""),
            "steps": [],
            "common_errors": [],
            "figure_url": q.get("figure_url", ""),
            "figure_description": q.get("figure_description", ""),
            "exam_frequency": q.get("exam_frequency", ""),
        })
        matched += 1

    print(f"  {subject}: {len(questions)}题 → 匹配{matched}题")
    return result


def main():
    all_questions = []
    for subject in ["math", "physics", "chemistry", "english"]:
        all_questions.extend(process_subject(subject))

    print(f"\n总计: {len(all_questions)}道真题已匹配node_id")

    # 输出到 exam-questions-mapped.json
    for subject in ["math", "physics", "chemistry", "english"]:
        subj_qs = [q for q in all_questions if q["id"].startswith(subject)]
        if subj_qs:
            out = DATA_DIR / subject / "questions-exam.json"
            out.write_text(json.dumps(subj_qs, ensure_ascii=False, indent=2))
            print(f"  写入 {out.name}: {len(subj_qs)}题")


if __name__ == "__main__":
    main()

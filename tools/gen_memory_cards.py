import sys
sys.stdout = open(sys.stdout.fileno(), mode="w", buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode="w", buffering=1)
"""记忆卡片 AI 批量生产工具
生成约3300张艾宾浩斯记忆卡片 + 英语单词TTS音频
"""
import json, time, re, hashlib, subprocess, os
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
AUDIO_DIR = ROOT / "data" / "memory-audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# 读.env
env = {}
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

API_KEY = env.get("MINIMAX_API_KEY", "")
API_BASE = env.get("OPENAI_API_BASE", "https://api.minimax.chat/v1")
MODEL = "MiniMax-M3"  # M2.7-highspeed token不够，用M3


def call_ai(prompt: str, max_retries=3) -> str:
    for attempt in range(max_retries):
        try:
            resp = httpx.post(
                f"{API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={"model": MODEL, "messages": [
                    {"role": "system", "content": "你是记忆卡片生成器。直接输出JSON数组，不要解释。"},
                    {"role": "user", "content": prompt}
                ], "max_tokens": 8192},
                timeout=300
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                if "<think>" in content:
                    content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
                return content
            elif resp.status_code == 429:
                time.sleep(10 * (attempt + 1))
            else:
                time.sleep(5)
        except Exception as e:
            print(f"  请求异常: {e}")
            time.sleep(5)
    return ""


def parse_cards(text: str) -> list:
    """解析AI返回的卡片JSON"""
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
    if text.endswith("```"):
        text = text[:-3]
    try:
        cards = json.loads(text.strip())
        if isinstance(cards, dict):
            cards = cards.get("cards", [])
        return [c for c in cards if isinstance(c, dict) and c.get("front") and c.get("back")]
    except:
        return []


def gen_english_vocab():
    """生成英语词汇卡片"""
    print("📝 英语词汇...")
    all_cards = []
    prompt_template = """你是初中英语教师。请生成{n}个初中英语必背单词的记忆卡片。
范围：{scope}

输出JSON数组，每张卡片：
{{"front": "英文单词", "back": "词性. 中文释义; 常用短语", "difficulty": 1-3}}

difficulty: 1=基础词(七年级) 2=核心词(八年级) 3=进阶词(九年级)
back格式示例: "n. 环境; protect the environment"
只输出JSON数组。"""

    scopes = [
        ("七年级上册核心词汇(家庭/学校/日常生活/食物/颜色/数字)", 25),
        ("七年级下册核心词汇(交通/天气/动物/职业/城市)", 25),
        ("八年级上册核心词汇(旅行/健康/科技/环境/文化)", 25),
        ("八年级下册核心词汇(社会/情感/教育/自然/历史)", 25),
        ("九年级核心词汇(梦想/挑战/合作/创新/全球化)", 25),
        ("中考高频动词(不规则变化/易混淆词)", 20),
        ("中考高频形容词和副词", 20),
        ("中考高频名词(抽象概念/社会话题)", 20),
        ("中考完形填空高频词汇", 20),
        ("中考阅读理解高频词汇", 20),
        ("初中英语短语动词(phrasal verbs)", 15),
        ("初中英语易混淆词辨析(affect/effect, accept/except等)", 15),
        ("七年级基础词汇补充(身体部位/服装/运动/学科)", 25),
        ("八年级词汇补充(情绪/性格/社交/媒体/经济)", 25),
        ("九年级词汇补充(科学/法律/政府/国际关系)", 25),
        ("中考写作高频词汇和表达", 20),
        ("初中英语前缀后缀派生词(un-/re-/dis-/-tion/-ment/-ness)", 20),
        ("中考必背固定搭配(介词短语/动词短语)", 20),
        ("初中英语同义词替换(good→excellent, big→enormous等)", 15),
        ("初中英语反义词配对", 15),
        ("初中英语熟词生义(常见词的不常见含义)", 15),
        ("中考真题高频生词(近5年武汉中考)", 20),
        ("初中英语话题词汇:环保与可持续发展", 15),
        ("初中英语话题词汇:科技与互联网", 15),
        ("初中英语话题词汇:传统文化与节日", 15),
        ("初中英语话题词汇:志愿服务与社会责任", 15),
        ("初中英语话题词汇:健康与饮食", 15),
        ("初中英语话题词汇:旅游与地理", 15),
        ("初中英语连接词和过渡词(however/therefore/meanwhile等)", 25),
        ("中考听力高频场景词汇(购物/问路/就医/预约)", 35),
    ]

    for scope, n in scopes:
        prompt = prompt_template.format(n=n, scope=scope)
        result = call_ai(prompt)
        cards = parse_cards(result)
        for c in cards:
            c["subject"] = "english"
            c["category"] = "vocab"
        all_cards.extend(cards)
        print(f"  {scope[:20]}... → {len(cards)}张")
        time.sleep(1)

    return all_cards


def gen_english_grammar():
    """生成英语语法卡片"""
    print("📝 英语语法...")
    prompt = """你是初中英语语法教师。生成200张初中英语语法记忆卡片，覆盖中考所有语法点。

每张卡片：
{"front": "语法规则/句型", "back": "解释 + 例句", "difficulty": 1-3}

涵盖：时态(8种)、被动语态、情态动词、定语从句、宾语从句、条件状语从句、比较级最高级、
非谓语动词、主谓一致、there be、反义疑问句、感叹句、倒装句等。

只输出JSON数组。"""
    
    all_cards = []
    # 分批生成
    topics = [
        "一般现在时/一般过去时/一般将来时的构成和用法(各8张)",
        "现在进行时/过去进行时/现在完成时的构成和用法(各8张)", 
        "被动语态(一般现在/过去/将来)的构成和用法(10张)",
        "情态动词(can/could/may/might/must/should/need)用法辨析(12张)",
        "宾语从句(that/if/whether/wh-引导)的时态呼应和语序(10张)",
        "定语从句(who/which/that/whose/where/when)的用法(12张)",
        "条件状语从句(if/unless)+时间状语从句(when/while/as soon as)(10张)",
        "形容词副词比较级最高级(规则变化/不规则/as...as/the more...the more)(10张)",
        "非谓语动词(to do/doing/done)作主语宾语定语补语(10张)",
        "特殊句式(there be/感叹句/反义疑问句/倒装句/强调句)(10张)",
    ]
    
    for topic in topics:
        p = f"生成初中英语语法卡片：{topic}\n每张：{{\"front\":\"规则\",\"back\":\"解释+例句\",\"difficulty\":1-3}}\n只输出JSON数组。"
        result = call_ai(p)
        cards = parse_cards(result)
        for c in cards:
            c["subject"] = "english"
            c["category"] = "grammar"
        all_cards.extend(cards)
        print(f"  {topic[:25]}... → {len(cards)}张")
        time.sleep(1)

    return all_cards


def gen_history():
    """生成历史卡片"""
    print("📝 历史事件...")
    all_cards = []
    
    topics = [
        ("中国古代史:夏商周秦(重要事件/人物/制度)", 20),
        ("中国古代史:汉唐(丝绸之路/贞观之治/科举制等)", 20),
        ("中国古代史:宋元明清(经济重心南移/郑和下西洋/闭关锁国等)", 20),
        ("中国近代史:鸦片战争→辛亥革命(不平等条约/洋务运动/戊戌变法)", 25),
        ("中国近代史:新文化运动→新中国成立(五四/建党/长征/抗战/解放)", 25),
        ("中国现代史:建国→改革开放(土改/一五计划/文革/十一届三中全会)", 20),
        ("世界古代史:四大文明古国/古希腊罗马", 15),
        ("世界近代史:文艺复兴/新航路/工业革命/法国大革命/美国独立", 20),
        ("世界现代史:一战/二战/冷战/联合国/全球化", 20),
        ("中考必考时间线(按年份排序的关键事件)", 20),
        ("中考必考历史人物(功绩+时代)", 15),
        ("中考必考制度/文献(《南京条约》《马关条约》等)", 15),
    ]

    for topic, n in topics:
        p = f"""生成{n}张初中历史记忆卡片：{topic}
每张：{{"front": "事件/人物/概念", "back": "时间+内容+意义(简洁)", "difficulty": 1-3}}
只输出JSON数组。"""
        result = call_ai(p)
        cards = parse_cards(result)
        for c in cards:
            c["subject"] = "history"
            c["category"] = "events"
        all_cards.extend(cards)
        print(f"  {topic[:25]}... → {len(cards)}张")
        time.sleep(1)

    return all_cards


def gen_politics():
    """生成道法卡片"""
    print("📝 道法要点...")
    all_cards = []

    topics = [
        ("心理健康:自我认识/情绪管理/挫折应对/青春期", 15),
        ("道德:诚信/友善/感恩/责任/公德", 15),
        ("法治:宪法/公民权利义务/未成年人保护/违法犯罪", 25),
        ("国情:基本国策/发展战略/社会主义核心价值观", 20),
        ("国情:基本政治制度(人大/政协/民族区域自治)", 15),
        ("国情:基本经济制度/分配制度/社会保障", 15),
        ("社会:创新/民主/法治/和谐/共享发展理念", 15),
        ("国际:和平与发展/人类命运共同体/中国担当", 15),
        ("中考高频考点:宪法核心知识(20张)", 20),
        ("中考高频考点:权利与义务辨析(20张)", 20),
        ("中考主观题常用答题模板和关键词", 15),
        ("时政热点对应知识点(科技创新/乡村振兴/双碳/一带一路)", 15),
    ]

    for topic, n in topics:
        p = f"""生成{n}张初中道德与法治记忆卡片：{topic}
每张：{{"front": "概念/问题", "back": "定义+要点(分条,简洁)", "difficulty": 1-3}}
只输出JSON数组。"""
        result = call_ai(p)
        cards = parse_cards(result)
        for c in cards:
            c["subject"] = "politics"
            c["category"] = "concepts"
        all_cards.extend(cards)
        print(f"  {topic[:25]}... → {len(cards)}张")
        time.sleep(1)

    return all_cards


def gen_chinese_poetry():
    """生成语文古诗词卡片"""
    print("📝 语文古诗词...")
    all_cards = []

    topics = [
        ("七年级上册必背古诗词(观沧海/闻王昌龄左迁/次北固山下/天净沙秋思等)名句填空", 25),
        ("七年级下册必背古诗词(木兰诗/登幽州台歌/望岳/游山西村等)名句填空", 25),
        ("八年级上册必背古诗词(野望/黄鹤楼/使至塞上/渡荆门送别/钱塘湖春行等)", 25),
        ("八年级下册必背古诗词(关雎/蒹葭/送杜少府/望洞庭湖/茅屋为秋风所破歌等)", 25),
        ("九年级上册必背古诗词(行路难/酬乐天/水调歌头/岳阳楼记等)", 25),
        ("九年级下册必背古诗词(鱼我所欲也/送东阳马生序/出师表等)名句填空", 25),
        ("初中文言文名句(陋室铭/爱莲说/醉翁亭记/小石潭记/记承天寺夜游等)", 25),
        ("古诗词作者+朝代+风格配对", 20),
        ("古诗词意象含义(月→思乡/柳→送别/梅→高洁等)", 15),
        ("古诗词理解性默写(给情境写出对应诗句)", 25),
        ("易错字词默写(通假字/生僻字/易写错的字)", 20),
        ("文言文重点实词虚词(之/而/以/于/其/为)", 20),
        ("中考必考文言文段落翻译要点", 20),
        ("古诗词鉴赏术语(借景抒情/托物言志/动静结合/虚实结合等)", 15),
    ]

    for topic, n in topics:
        p = f"""生成{n}张初中语文古诗文记忆卡片：{topic}
每张：{{"front": "上句___/篇名/填空题", "back": "完整答案", "difficulty": 1-3}}
注意：默写题front留空让学生填，back给完整答案。
只输出JSON数组。"""
        result = call_ai(p)
        cards = parse_cards(result)
        for c in cards:
            c["subject"] = "chinese"
            c["category"] = "poetry"
        all_cards.extend(cards)
        print(f"  {topic[:25]}... → {len(cards)}张")
        time.sleep(1)

    return all_cards


def gen_tts(cards: list):
    """为英语词汇生成TTS音频"""
    print("\n🔊 生成英语TTS音频...")
    vocab_cards = [c for c in cards if c.get("subject") == "english" and c.get("category") == "vocab"]
    print(f"  需要生成: {len(vocab_cards)}个单词")

    generated = 0
    for c in vocab_cards:
        word = c["front"].strip()
        # 文件名用hash
        fname = hashlib.md5(word.encode()).hexdigest()[:10] + ".mp3"
        fpath = AUDIO_DIR / fname
        if fpath.exists():
            c["audio_url"] = f"/memory-audio/{fname}"
            continue
        try:
            subprocess.run(
                ["edge-tts", "--voice", "en-US-AriaNeural", "--text", word, "--write-media", str(fpath)],
                capture_output=True, timeout=10
            )
            if fpath.exists():
                c["audio_url"] = f"/memory-audio/{fname}"
                generated += 1
        except:
            pass

    print(f"  生成完成: {generated}个新音频")


def main():
    print("=" * 50)
    print("记忆卡片批量生产")
    print("=" * 50)

    all_cards = []

    # 1. 英语词汇
    vocab = gen_english_vocab()
    all_cards.extend(vocab)
    print(f"  英语词汇: {len(vocab)}张\n")

    # 2. 英语语法
    grammar = gen_english_grammar()
    all_cards.extend(grammar)
    print(f"  英语语法: {len(grammar)}张\n")

    # 3. 历史
    history = gen_history()
    all_cards.extend(history)
    print(f"  历史: {len(history)}张\n")

    # 4. 道法
    politics = gen_politics()
    all_cards.extend(politics)
    print(f"  道法: {len(politics)}张\n")

    # 5. 语文古诗词
    poetry = gen_chinese_poetry()
    all_cards.extend(poetry)
    print(f"  语文: {len(poetry)}张\n")

    # 6. TTS
    gen_tts(all_cards)

    # 给每张卡片生成唯一ID
    for i, c in enumerate(all_cards):
        c["id"] = i + 1

    # 保存
    out_path = DATA_DIR / "memory-cards.json"
    out_path.write_text(json.dumps(all_cards, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*50}")
    print(f"总计: {len(all_cards)}张卡片")
    print(f"保存: {out_path}")
    subjects = {}
    for c in all_cards:
        s = c.get("subject", "?")
        subjects[s] = subjects.get(s, 0) + 1
    for s, n in sorted(subjects.items()):
        print(f"  {s}: {n}张")


if __name__ == "__main__":
    main()

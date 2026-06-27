"""从 teachany.cn 下载课件并自托管。

用法：
  python3 tools/fetch_courseware.py <course_id> <subject> <node_id>
例：
  python3 tools/fetch_courseware.py math-linear-function math math-m-linear-function

产物：
  courseware/<subject>/<node_id>/index.html  (+ assets/ + tts/)
  courseware/_assets/scripts/*                (共享平台脚本，所有课件复用)

重写：index.html 中绝对路径 /assets/scripts/ → /courseware/_assets/scripts/
geogebra 等 CDN 资源保持外链。
"""
import re
import sys
import urllib.request
from pathlib import Path

SITE = "https://www.teachany.cn"
ROOT = Path(__file__).parent.parent
CW = ROOT / "courseware"

# 共享平台脚本（站点根 /assets/scripts/），所有课件复用
SHARED_SCRIPTS = [
    "ai-tutor.js", "ai-tutor.css",
    "feedback-widget.js",
    "teachany-audio-player.js", "teachany-audio-player.css",
    "teachany-knowledge-graph.js", "teachany-knowledge-graph.css",
    "teachany-section-hints.js", "teachany-section-hints.css",
    "teachany-tts-narrator.js", "teachany-tts-narrator.css",
    "teachany-tutor-card.js", "teachany-tutor-card.css",
    "teachany-floating-dock.css",
]


def fetch(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.read()
    except Exception as e:
        print(f"    ✗ {url} : {e}")
        return None


def save(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main():
    if len(sys.argv) < 4:
        print("用法: fetch_courseware.py <course_id> <subject> <node_id>")
        sys.exit(1)
    course_id, subject, node_id = sys.argv[1], sys.argv[2], sys.argv[3]
    base = f"{SITE}/community/{course_id}/"
    dest = CW / subject / node_id
    print(f"课件: {course_id} → {dest.relative_to(ROOT)}")

    # 1. index.html
    html = fetch(base + "index.html") or fetch(base)
    if not html:
        print("  ✗ 无法获取 index.html"); sys.exit(1)
    text = html.decode("utf-8", errors="replace")

    # 2. 课件内相对资源（assets/*, tts/*）——全文匹配，兼容 HTML属性 与 JS字符串
    rels = set(re.findall(
        r'\.?/?((?:assets|tts)/[\w./-]+\.(?:png|jpe?g|webp|svg|gif|mp3|wav|json|js|css))',
        text))
    got, want = 0, 0
    for clean in rels:
        if clean.startswith("assets/scripts/"):
            continue  # 共享脚本单独处理
        want += 1
        data = fetch(base + clean)
        if data:
            save(dest / clean, data)
            got += 1
    print(f"  课件资源 {got}/{want} 个")

    # 3. manifest（可选）
    mani = fetch(base + "manifest.json")
    if mani:
        save(dest / "manifest.json", mani)

    # 4. 共享平台脚本（下载一次到 _assets/scripts/）
    shared_dir = CW / "_assets" / "scripts"
    sn = 0
    for s in SHARED_SCRIPTS:
        if (shared_dir / s).exists():
            sn += 1; continue
        data = fetch(f"{SITE}/assets/scripts/{s}")
        if data:
            save(shared_dir / s, data); sn += 1
    print(f"  共享脚本 {sn}/{len(SHARED_SCRIPTS)} 个 (courseware/_assets/scripts/)")

    # 5. 重写绝对路径 /assets/scripts/ → /courseware/_assets/scripts/
    text = text.replace('"/assets/scripts/', '"/courseware/_assets/scripts/')
    text = text.replace('="assets/scripts/', '="/courseware/_assets/scripts/')

    # 5b. 移除 teachany 外部导航（Gallery/Path等跳转到 teachany.cn 的链接块）
    text = re.sub(r'<!-- teachany-back-to-gallery -->.*?<!-- /teachany-back-to-gallery -->', '', text, flags=re.DOTALL)

    # 6. 注入 AI学伴代理配置（指向自建后端 /api/tutor，key留服务端）
    inject = (
        "<script>(function(){try{var K='teachany_tutor_config';"
        "if(!localStorage.getItem(K)){localStorage.setItem(K,JSON.stringify("
        "{provider:'custom',baseUrl:location.origin+'/api/tutor/v1',"
        "apiKey:'self-hosted',model:'MiniMax-Text-01'}));}}catch(e){}})();</script>"
    )
    if "teachany_tutor_config" not in text:
        text = text.replace("<head>", "<head>\n" + inject, 1)

    save(dest / "index.html", text.encode("utf-8"))
    print(f"  ✅ index.html 已重写+注入学伴配置并保存")
    print(f"\n访问: /courseware/{subject}/{node_id}/index.html")


if __name__ == "__main__":
    main()

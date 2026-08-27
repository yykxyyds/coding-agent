"""联网抓取辅助命令（供 agent 通过 run_bash 调用，纯标准库）。

用法：
  python web_fetch.py --search "关键词"   # Bing 搜索，返回标题/链接/摘要列表
  python web_fetch.py <URL>               # 抓取一个网页，输出净化后的正文文本
"""
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
TIMEOUT = 20
MAX_OUT = 6000


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    return urllib.request.urlopen(req, timeout=TIMEOUT).read()


def html_to_text(html):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</(p|div|tr|h[1-6]|li)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    for ent, ch in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                    ("&nbsp;", " "), ("&#39;", "'")):
        text = text.replace(ent, ch)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def search(query):
    url = "https://cn.bing.com/search?q=" + urllib.parse.quote(query)
    html = fetch(url).decode("utf-8", "replace")
    blocks = re.findall(r'<li class="b_algo".*?</li>', html, re.S)
    if not blocks:
        return f"（搜索无结构化结果，关键词: {query}）"
    lines = []
    for b in blocks[:5]:
        m = re.search(r'<h2[^>]*>\s*<a[^>]*href="(https?[^"]+)"[^>]*>(.*?)</a>', b, re.S)
        href = m.group(1) if m else "?"
        title = re.sub(r"<[^>]+>", "", m.group(2)).strip() if m else "?"
        p = re.search(r"<p[^>]*>(.*?)</p>", b, re.S)
        snip = re.sub(r"<[^>]+>", "", p.group(1)).strip() if p else ""
        lines.append(f"- {title}\n  链接: {href}\n  摘要: {snip[:150]}")
    return "\n\n".join(lines)


def main(argv):
    if not argv:
        print(__doc__)
        return
    try:
        if argv[0] == "--search":
            out = search(" ".join(argv[1:]))
        else:
            raw = fetch(argv[0])
            text = html_to_text(raw.decode("utf-8", "replace"))
            out = f"[{argv[0]}] 页面正文（已净化）:\n{text}"
        if len(out) > MAX_OUT:
            out = out[:MAX_OUT] + f"\n…[输出过长，已截断]"
        print(out)
    except Exception as e:
        print(f"[错误] 联网失败: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main(sys.argv[1:])

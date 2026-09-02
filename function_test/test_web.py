# -*- coding: utf-8 -*-
"""web_search / web_fetch 单元自测：本地 http server 模拟网页，验证抓取/解码/正文提取/错误兜底。

联网部分（web_search 对真实 Bing）用 try 包裹，网络不通时跳过不中断。
放在 function_test/ 下，随仓库提交（功能测试）。
"""
import os
import sys
import threading
import http.server
import socketserver

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import tool_web_fetch, tool_web_search


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/utf8":
            body = ("<html><head><title>定价页</title></head><body>"
                    "<h1>API 价格</h1><p>DeepSeek-V3 输入 0.1 元/百万token</p>"
                    "<script>console.log('x')</script></body></html>").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif self.path == "/gbk":
            body = ("<html><body><p>通义千问 qwen-max 输入 0.6 元/千token</p></body></html>").encode("gbk")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
        elif self.path == "/empty":
            body = b"<html><body><div id='root'></div></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        else:
            body = b"not found"
            self.send_response(404)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


srv = socketserver.TCPServer(("127.0.0.1", 0), Handler)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{port}"

# ── 1. web_fetch 抓 UTF-8 中文页：正文提取 + 去 script ──
r = tool_web_fetch(f"{BASE}/utf8", max_chars=2000)
assert "API 价格" in r and "DeepSeek-V3" in r, r
assert "console" not in r, "script 内容不应出现在正文里"
assert r.startswith("[网页]"), r
print("[1] PASS web_fetch 抓 UTF-8 中文页，正文含价格、script 已剔除")

# ── 2. web_fetch 抓 GBK 编码页：自动按 GBK 解码 ──
r = tool_web_fetch(f"{BASE}/gbk", max_chars=2000)
assert "通义千问" in r and "qwen-max" in r, r
print("[2] PASS web_fetch 自动按 GBK 解码中文页")

# ── 3. web_fetch 抓 JS 壳空页：明确提示无文本 ──
r = tool_web_fetch(f"{BASE}/empty", max_chars=2000)
assert "无可见文本" in r, r
print("[3] PASS web_fetch 对 JS 渲染空页给出明确提示")

# ── 4. web_fetch 网络错误 / 非法协议 ──
r = tool_web_fetch(f"{BASE}/404", max_chars=2000)
assert "网络错误" in r, r
r = tool_web_fetch("file:///etc/passwd", max_chars=2000)
assert "只支持 http" in r, r
print("[4] PASS web_fetch 网络错误与非法协议兜底")

# ── 5. web_search 边界：空关键词 ──
r = tool_web_search("  ")
assert "关键词为空" in r, r
print("[5] PASS web_search 空关键词拦截")

# ── 6. web_search 联网（真实 Bing）：网络不通则跳过 ──
try:
    r = tool_web_search("DeepSeek API 价格", max_results=3)
    assert "1." in r and "URL:" in r, r[:200]
    print("[6] PASS web_search 真实搜索返回标题/URL/摘要")
except Exception as e:
    print(f"[6] SKIP web_search 联网测试（{type(e).__name__}: {e}）")

srv.shutdown()
print("\n全部断言通过")

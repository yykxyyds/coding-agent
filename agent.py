"""编程智能体：通过与大语言模型交互，自主读写文件、执行命令，完成编程任务。

核心是一个 agent loop（想→做→看结果→再想，直到完成）：
  - 对话历史与上下文管理：_trim_history
  - 工具的定义与本地执行：TOOLS + execute_tool
  - 模型输出的解析：LLMClient.chat 解析 tool_calls
  - 循环终止条件：无 tool_call 即停 + max_steps 保护
  - 错误处理：命令超时、文件异常、API 失败

仅依赖 Python 标准库。真实调用 DeepSeek；无 key 时可用 --mock 模拟。
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from llm import LLMClient, LLMError, MockLLM

# 两个关键常量：控制"回传给模型的内容大小"和"单条命令的执行时长"
MAX_OUTPUT = 8000      # 工具结果返回给模型的内容上限（字符），防止上下文被单条长输出塞爆
CMD_TIMEOUT = 60       # 单条命令超时（秒），防止命令无限卡住

# 上下文预算（无 token 计算库，用字符数近似 token 占用；中文约 1 字符≈1 token）
MAX_HISTORY_CHARS = 200000   # 历史总字符数超过则触发压缩；对 128K/1M 上下文均留足余量，可经 --max-history-chars 覆盖
MAX_HISTORY_MSGS = 600       # 消息条数绝对护栏：防止大量极短消息绕过字符预算
KEEP_RECENT_ROUNDS = 15      # 压缩时保留的最近完整轮数（活动区；上下文窗口越大应越大）
MAX_STEPS = 200              # 默认最大循环步数（安全阀，防死循环）：配合 compact 上下文不会爆，正常任务极少触顶

# 联网调研（web 工具）参数
WEB_TIMEOUT = 15      # 单次联网请求超时（秒）：厂商定价页/搜索偶有慢，留足时间又不会卡死
WEB_MAX_CHARS = 6000  # web_fetch 返回正文上限（字符）：网页正文动辄几万字，截断防上下文爆掉
MAX_LOOP_ROUNDS = 100  # /loop 定时执行的最大轮数护栏：防忘记停导致挂机

SYSTEM_PROMPT = """你是编程智能体，负责在本地工作目录 {workdir} 中完成用户交给的编程任务。
你可以通过调用工具来操作电脑：
- run_bash：执行 shell 命令（Windows 环境，列目录用 dir；可用 python 运行/测试程序）
- read_file：读取文本文件
- write_file：写入或覆盖文本文件
- web_search：联网搜索，返回结果标题/URL/摘要（调研、查资料、找官方页面用）
- web_fetch：抓取一个网页的正文纯文本（读定价页、文档、新闻内容）

工作规则：
1. 动手前先了解现状：先查看目录和关键文件，再开始改动。
2. 每做一步就验证：写完代码运行一下，有报错就读取报错并修正。
3. 只修改工作目录内的文件。
4. 任务确认完成、验证通过后，用自然语言给出最终总结（做了什么、结果如何）。
5. 命令输出可能被截断，注意提示。"""

# 工具定义（JSON schema）：随请求发给模型，让它知道"有哪些工具可用、参数长什么样"
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "执行一条 shell 命令（Windows cmd），用于列目录、运行程序、执行测试等。返回命令输出。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的完整命令行，如 dir 或 python counter.py data.txt"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取工作目录内一个文本文件的完整内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径（相对工作目录）"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入或覆盖工作目录内的一个文本文件。父目录不存在会自动创建。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径（相对工作目录）"},
                    "content": {"type": "string", "description": "文件的完整内容"}
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "联网搜索：向搜索引擎查询关键词，返回最多 10 条结果的标题、URL、摘要。用于调研、查资料、找官方定价/文档页面。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词，中文或英文，尽量具体（如'阿里云百炼 qwen API 价格'）"},
                    "max_results": {"type": "integer", "description": "返回结果条数，默认 8"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "抓取一个网页并返回正文纯文本。用于读取搜索结果中的具体页面（定价页、文档、新闻）。对 JS 动态渲染的空页面会明确提示。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "网页 URL（http/https）"},
                    "max_chars": {"type": "integer", "description": "最多返回的字符数，默认 6000"}
                },
                "required": ["url"],
            },
        },
    },
]


def _safe_path(workdir, path):
    """路径沙箱：把 path 限制在工作目录内，越界返回 None。

    三个文件工具都先过这里，防止模型读写工作目录之外的敏感文件。
    """
    ap = os.path.abspath(os.path.join(workdir, path))
    wd = os.path.abspath(workdir)
    norm_wd = os.path.normcase(wd)
    norm_ap = os.path.normcase(ap)
    if norm_ap != norm_wd and not norm_ap.startswith(norm_wd + os.sep):
        return None
    return ap


def _decode_bytes(raw):
    """Windows 适配：cmd 输出常为 GBK、Python 输出常为 UTF-8，按序尝试解码。"""
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _clean_text(s):
    """剔除字符串里的孤立代理字符（Windows 终端/管道编码错配时 input 可能读到 surrogate），
    避免其污染上下文或让 JSON 落盘崩溃；编码错配造成的乱码中文无法自动纠正，靠终端编码一致保证。"""
    return s.encode("utf-8", "replace").decode("utf-8")


def tool_run_bash(command, workdir):
    """工具①：执行一条 shell 命令，返回输出文本（含超时、截断兜底）。"""
    # ── 第 1 步：空命令防御 ──
    # 模型偶尔会给出空串/纯空格命令，直接执行只会浪费一轮循环；
    # 提前拦下，返回错误串让模型自己意识到问题、重新给命令。
    if not command or not command.strip():
        return "[错误] 命令为空。"

    # ── 第 2 步：真正执行命令 ──
    try:
        proc = subprocess.run(
            command, shell=True, cwd=workdir,   # shell=True：Windows 下把命令交给 cmd 执行
            capture_output=True, timeout=CMD_TIMEOUT,  # 捕获输出不刷屏 + 超 60 秒强制掐断
        )
    except subprocess.TimeoutExpired:
        # 命令超时被中止：明确告诉模型超时了，建议拆小任务或换更快的命令
        return f"[命令超时] 超过 {CMD_TIMEOUT} 秒已中止，请把任务拆小或简化命令。"

    # ── 第 3 步：把字节解码成字符串 ──
    # proc.stdout/stderr 是 bytes，编码不确定（cmd 内建命令=GBK、python 脚本=UTF-8），
    # 合并后交给 _decode_bytes 按 UTF-8→GBK 依次试解。
    # "or b''" 兜底：命令没输出时 proc.stdout 是 None，None+bytes 会报错，用空字节代替。
    out = _decode_bytes((proc.stdout or b"") + (proc.stderr or b""))

    # ── 第 4 步：清理 + 分类处理 ──
    out = out.strip()                          # 去掉首尾多余空白，让输出更干净
    if not out:
        # 命令执行完但没输出（如重定向到文件）：报出退出码，
        # 模型至少能判断"命令跑完了"还是"命令出错被拦"
        out = f"（命令执行完成，退出码 {proc.returncode}，无输出）"
    elif len(out) > MAX_OUTPUT:
        # 输出超过 8000 字符：只留前 8000，并【明示】被截掉了多少。
        # 为什么必须明示：模型看到"已截断 N 字符"，才知道信息不完整，
        # 才会主动换命令（如 grep、find）去拿关键内容，而不是误以为这就是全部结果。
        out = out[:MAX_OUTPUT] + f"\n…[输出过长，已截断 {len(out) - MAX_OUTPUT} 字符]"
    return out


def tool_read_file(path, workdir):
    """工具②：读取工作目录内的文本文件（越界拒绝、超长截断）。"""
    fp = _safe_path(workdir, path)
    if fp is None:
        return "[错误] 路径越界，只能访问工作目录内的文件。"
    if not os.path.isfile(fp):
        return f"[错误] 文件不存在: {path}"
    try:
        with open(fp, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return f"[错误] 读取失败: {e}"
    if len(content) > MAX_OUTPUT:
        content = content[:MAX_OUTPUT] + f"\n…[内容过长，已截断]"
    return content


def tool_write_file(path, content, workdir):
    """工具③：写入/覆盖工作目录内的文件（父目录自动创建，返回短确认）。"""
    # ── 第 1 步：路径沙箱检查 ──
    # _safe_path 把 path 规范化后，确认它落在工作目录内；
    # 越界（如 ../DeepSeekAPI.txt）返回 None → 拒绝写入，防止模型篡改工作目录外的文件。
    fp = _safe_path(workdir, path)
    if fp is None:
        return "[错误] 路径越界，只能写工作目录内的文件。"

    # ── 第 2 步：自动创建父目录 ──
    # dirname 取出文件所在目录；exist_ok=True 表示目录已存在也不报错，
    # 这样模型写 sub/new.py 这类深层路径时，父目录不存在也能一次成功。
    parent = os.path.dirname(fp)
    if parent:
        os.makedirs(parent, exist_ok=True)

    # ── 第 3 步：写入文件 ──
    # "w" = 覆盖写入（文件已存在则清空重写）；encoding="utf-8" 统一用 UTF-8 存盘，保证中英文内容一致。
    # try/except 兜底：磁盘满、权限不足等异常不崩溃，转成错误字符串回传给模型，让它知道写失败了。
    try:
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return f"[错误] 写入失败: {e}"

    # ── 第 4 步：返回短确认 ──
    # 不把整个文件内容回传（浪费上下文），只报"写入了哪个文件、多少字符"，
    # 模型据此确认写入成功，继续下一步。
    return f"已写入文件 {path}（{len(content)} 字符）。"


# ── 联网调研：web_search / web_fetch ──
# 调研类任务（如"联网查 API 价格")原来只能靠 run_bash 手拼 requests 脚本，
# 脆弱且浪费步数；这两个工具用标准库直连，让 agent 能"先搜索发现页面、再抓正文"。


def _http_get(url, timeout=WEB_TIMEOUT):
    """urllib 抓取 URL 返回 bytes；失败把错误转成文本 bytes 返回（不抛异常，错误流向工具结果）。"""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        return urllib.request.urlopen(req, timeout=timeout).read()
    except Exception as e:
        return f"[网络错误] {type(e).__name__}: {e}".encode("utf-8")


def _decode_http(raw):
    """网页字节解码：按 UTF-8 → GBK 试解（中文站多为 GBK），都失败用替换符兜底。"""
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _html_to_text(html_text):
    """HTML → 纯文本：删 script/style/head 等、块级标签换行、去标签、反转义、压空行。"""
    html_text = re.sub(r"(?is)<(script|style|noscript|head|iframe)[^>]*>.*?</\1>", " ", html_text)
    html_text = re.sub(r"(?i)<(br|/p|/div|/li|/h[1-6]|/tr|/table|/ul|/ol)[^>]*>", "\n", html_text)
    html_text = re.sub(r"<[^>]+>", " ", html_text)
    text = html.unescape(html_text)
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def tool_web_search(query, max_results=8):
    """工具④：联网搜索（Bing RSS 端点，返回真实 URL，纯标准库解析 XML）。
    max_results 限制在 1~10，结果按 标题/URL/摘要 逐条列出。"""
    if not query or not query.strip():
        return "[错误] 搜索关键词为空。"
    url = ("https://www.bing.com/search?q=" + urllib.parse.quote(query.strip())
           + "&format=rss&count=10")
    raw = _http_get(url)
    text = _decode_http(raw)
    if text.startswith("[网络错误]"):
        return text
    try:
        root = ET.fromstring(text)
        items = root.findall(".//item")
    except Exception as e:
        return f"[错误] 搜索解析失败: {e}"
    if not items:
        return "[结果] 无搜索结果，换个关键词重试。"
    max_results = max(1, min(int(max_results or 8), 10))
    out = []
    for i, item in enumerate(items[:max_results], 1):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = re.sub(r"\s+", " ", (item.findtext("description") or "")).strip()[:200]
        out.append(f"{i}. {title}\n   URL: {link}\n   摘要: {desc}")
    return "\n\n".join(out)


def tool_web_fetch(url, max_chars=WEB_MAX_CHARS):
    """工具⑤：抓取网页正文纯文本。JS 渲染的空页面会明确提示，引导模型换数据来源。"""
    if not url.startswith(("http://", "https://")):
        return "[错误] 只支持 http/https 链接。"
    raw = _http_get(url)
    text = _decode_http(raw)
    if text.startswith("[网络错误]"):
        return text
    body = _html_to_text(text)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    if not body:
        return "[结果] 页面无可见文本（可能是 JS 动态渲染），请换搜索结果里的其他来源或换关键词。"
    if len(body) > max_chars:
        body = body[:max_chars] + f"\n…[内容过长，已截断 {len(body) - max_chars} 字符]"
    return f"[网页] {url}\n\n{body}"


def execute_tool(name, args, workdir):
    """分发器：按工具名调用对应实现；未知工具返回错误字符串（回传模型自我纠正）。

    用 args.get(...) 宽容取值——缺参数不崩，让错误自然流向执行结果。
    """
    if name == "run_bash":
        return tool_run_bash(args.get("command", ""), workdir)
    if name == "read_file":
        return tool_read_file(args.get("path", ""), workdir)
    if name == "write_file":
        return tool_write_file(args.get("path", ""), args.get("content", ""), workdir)
    if name == "web_search":
        return tool_web_search(args.get("query", ""), args.get("max_results", 8))
    if name == "web_fetch":
        return tool_web_fetch(args.get("url", ""), args.get("max_chars", WEB_MAX_CHARS))
    return f"[错误] 未知工具: {name}"


def _trim_history(messages, max_len=50):
    """上下文管理：历史超长时优先删最老的一整轮（assistant 的 tool_calls + 对应 tool 结果）。

    协议要求 tool 消息必须紧跟其 assistant 的 tool_calls，
    只删半边会留下孤立 tool 消息导致接口报错，所以删除单元必须是完整一轮。
    """
    while len(messages) > max_len:
        idx = None
        # 从最老开始找第一个带 tool_calls 的 assistant 消息
        for i in range(1, len(messages)):        # 从 1 开始：index 0 的 system 永不删
            if messages[i].get("role") == "assistant" and messages[i].get("tool_calls"):
                idx = i
                break
        if idx is None:
            # 没有工具调用轮（纯对话）：退化为删第一个 user/tool 消息
            for i in range(1, len(messages)):
                if messages[i]["role"] in ("user", "tool"):
                    del messages[i]
                    break
        else:
            # 找到一整轮：assistant + 它后面连续的所有 tool 结果一起删
            end = idx + 1
            while end < len(messages) and messages[end]["role"] == "tool":
                end += 1
            del messages[idx:end]
    return messages


# 参考 Claude Code 的 9 段压缩提示词，精简为 coding agent 最关键的 4 类信息
COMPACT_PROMPT = """你是上下文压缩器。下面是编程智能体（coding agent）的一段对话历史（JSON 数组，含 user/assistant/tool 消息）。请把它压缩成 300 字以内的中文摘要，供后续继续执行任务时参考。

摘要必须保留以下事实信息（出现过的不能丢，没有的可省略）：
1. 用户的原始请求与目标
2. 涉及的文件路径、关键代码片段或数据结构
3. 已执行的重要命令与结果、遇到的错误与修复方式
4. 尚未完成的待办事项、当前工作进度与下一步计划

要求：只输出摘要正文，不要多余解释；省略客套与重复，但保留最终结论。"""


def _summarize(llm, messages):
    """把一段历史交给模型总结成摘要；调用失败返回 None，由调用方降级为硬删。"""
    if not messages:
        return None
    # 控制请求体大小：每条 content 截断到 1000 字符、最多取末尾 100 条（越靠近活动区越关键），
    # 避免总结请求本身超出上下文
    view = []
    for m in messages[-100:]:
        msg = {"role": m.get("role", "user")}
        c = m.get("content") or ""
        if len(c) > 1000:
            c = c[:1000] + "\n…[已截断]"
        msg["content"] = c
        if m.get("tool_calls"):
            msg["tool_calls"] = m["tool_calls"]
        if m.get("tool_call_id"):
            msg["tool_call_id"] = m["tool_call_id"]
        view.append(msg)
    payload = [
        {"role": "system", "content": COMPACT_PROMPT},
        {"role": "user", "content": "以下是需要压缩的对话历史：\n" + json.dumps(view, ensure_ascii=False)},
    ]
    try:
        content, _ = llm.chat(payload, tools=None)
    except LLMError:
        return None
    content = (content or "").strip()
    return content or None


def _keep_start(messages, keep_recent):
    """从末尾往前数 keep_recent 个完整轮，返回保留区起点下标。

    一轮 = 一条非 tool 消息（user/assistant）+ 紧随其后的所有 tool 结果；
    保证保留区第一条不是孤立 tool 消息（协议要求 tool 紧跟其 assistant）。
    """
    n = len(messages)
    i = n - 1
    rounds = 0
    while i >= 1 and rounds < keep_recent:
        while i >= 1 and messages[i].get("role") == "tool":   # 跳过 tool，归入前一个 assistant 轮
            i -= 1
        if i < 1:
            break
        rounds += 1
        i -= 1
    return i + 1


def _history_chars(messages):
    """历史内容总字符数，近似上下文占用（无 token 库依赖）。"""
    return sum(len(m.get("content") or "") for m in messages)


def _compact_history(messages, llm, max_chars=MAX_HISTORY_CHARS, keep_recent=KEEP_RECENT_ROUNDS, force=False):
    """上下文管理：超长时压缩而非整轮删除（参考 Claude Code 的双区保留）。

    force=False（自动触发）：历史总字符超 max_chars，或条数超 MAX_HISTORY_MSGS 时压缩。
    force=True（手动 /compact）：跳过预算检查，无条件把更老的历史压缩成摘要。
    两者都保留最近 keep_recent 个完整轮次原样，摘要作为带边界标记的 user 消息前置到 system 之后；
    压缩调用失败或无可压内容时，自动模式降级为 _trim_history 硬删兜底，手动模式原样返回。
    """
    if not force and len(messages) <= MAX_HISTORY_MSGS and _history_chars(messages) <= max_chars:
        return messages
    keep_start = _keep_start(messages, keep_recent)
    if keep_start <= 1:
        # 历史太短（没有可压缩的旧轮次）：手动模式原样返回，自动模式降级硬删
        return messages if force else _trim_history(messages, MAX_HISTORY_MSGS)
    summary = _summarize(llm, messages[1:keep_start])
    if summary:
        compacted = [messages[0],
                     {"role": "user", "content": f"[先前对话已压缩，细节可能有损]\n{summary}"},
                     ] + messages[keep_start:]
        if force:
            return compacted
        if len(compacted) <= MAX_HISTORY_MSGS and _history_chars(compacted) <= max_chars:
            return compacted
    return messages if force else _trim_history(messages, MAX_HISTORY_MSGS)


def _interrupt_requested():
    """检测用户是否按了 ESC（Windows 标准库 msvcrt；非 Windows 恒为 False）。

    只认 ESC 为中断信号；运行中键入的其他字符被消耗丢弃，
    避免残留到后续 input() 造成任务文本混乱。
    """
    try:
        import msvcrt
    except ImportError:
        return False
    hit = False
    while msvcrt.kbhit():
        if msvcrt.getch() == b"\x1b":   # ESC 键
            hit = True
    return hit


# ── 会话持久化（resume）：对话历史统一存到项目根 session/<id>.json（不随 workdir 变，resume 永远找同一个目录）──
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session")


def _new_session_id():
    """会话 ID = 启动时刻时间戳（可排序，一眼看出先后）。"""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _session_dir():
    return SESSION_DIR


def _session_path(sid):
    return os.path.join(SESSION_DIR, f"{sid}.json")


def _save_session(sid, messages):
    os.makedirs(SESSION_DIR, exist_ok=True)
    with open(_session_path(sid), "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=True)   # ASCII 转义：任何字符（含代理字符）都能安全落盘


def _load_session(sid):
    p = _session_path(sid)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _list_sessions():
    """返回会话 ID 列表，最新在前。"""
    if not os.path.isdir(SESSION_DIR):
        return []
    return sorted((f[:-5] for f in os.listdir(SESSION_DIR) if f.endswith(".json")), reverse=True)


def _refresh_system(messages, workdir):
    """恢复会话时把 system 消息重建为当前工作目录的提示（原文件里可能是旧 workdir）。"""
    if messages and messages[0].get("role") == "system":
        messages[0]["content"] = SYSTEM_PROMPT.format(workdir=workdir)
    return messages


def _first_task(messages):
    """取会话首个用户任务的简短描述（供列表展示）。"""
    for m in messages:
        if m.get("role") == "user":
            c = (m.get("content") or "").strip()
            if c.startswith("[先前对话已压缩"):
                return "（已压缩的历史会话）"
            return c[:40]
    return ""


def _choose_session():
    """--resume：列出历史会话，用户输入序号选择；0 跳过。返回 (sid, messages) 或 (None, None)。"""
    sids = _list_sessions()
    if not sids:
        print("暂无历史会话（session/ 为空），开始全新会话。")
        return None, None
    print("历史会话（session/）：")
    for i, sid in enumerate(sids, 1):
        msgs = _load_session(sid) or []
        print(f"  [{i}] {sid}  {_first_task(msgs)}  ({len(msgs)} 条)")
    try:
        pick = input("输入序号恢复（0 跳过，开始新会话）: ").strip()
    except EOFError:
        return None, None
    if pick == "0":
        return None, None
    try:
        idx = int(pick) - 1
        if 0 <= idx < len(sids):
            return sids[idx], _load_session(sids[idx])
    except ValueError:
        pass
    print("输入无效，开始全新会话。")
    return None, None


def _print_available():
    sids = _list_sessions()
    if not sids:
        print("暂无历史会话。")
        return
    print("可用会话：")
    for sid in sids:
        print(f"  {sid}")


def run_agent(llm, task, workdir, max_steps=MAX_STEPS, verbose=True, compact=True, messages=None, max_chars=MAX_HISTORY_CHARS):
    """
    agent 主循环（全项目发动机）。
    流程：发历史+工具定义 → 模型返回 → 无工具调用即完成 / 有则本地执行+回填 → 循环。
    messages：传入已有会话历史则续跑（追加新任务），None 则新建会话；返回的 messages 供下次续跑。
    """
    if messages:
        messages = list(messages) + [{"role": "user", "content": task}]
    else:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(workdir=workdir)},
            {"role": "user", "content": task},
        ]
    final = None
    for step in range(1, max_steps + 1):
        if _interrupt_requested():                          # 用户按 ESC 可随时中断
            print("\n⏹ 检测到 ESC，任务已中止。")
            final = "（用户按 ESC 中断，任务未确认完成）"
            break
        if verbose:
            print(f"\n─── 第 {step} 步 ───")
        content, tool_calls = llm.chat(messages, tools=TOOLS)   # ① 发历史+工具定义

        if not tool_calls:                                      # ② 终止条件：无工具调用即完成
            final = content or "（模型未给出任何回复）"
            if verbose:
                print(f"[AI] {final}")
            break

        if content and verbose:
            print(f"[AI] {content}")    # 模型"边说话边调工具"的情况，两者都保留

        # ③ 协议要求：assistant 消息（含 tool_calls）先入历史，再放对应 tool 结果
        asst_msg = {"role": "assistant", "content": content}
        asst_msg["tool_calls"] = [
            {"id": tc["id"], "type": "function",
             "function": {"name": tc["name"],
                          "arguments": json.dumps(tc["arguments"], ensure_ascii=False)}}
            for tc in tool_calls
        ]
        messages.append(asst_msg)

        for tc in tool_calls:                                   # ④ 本地执行 + 结果回填
            name, args = tc["name"], tc["arguments"]
            if verbose:
                print(f"[工具] {name} {json.dumps(args, ensure_ascii=False)}")
            result = execute_tool(name, args, workdir)
            if verbose:
                preview = result.replace("\n", " | ")[:400]
                print(f"  ↳ {preview}")
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
        if compact:
            messages = _compact_history(messages, llm, max_chars=max_chars)  # ⑤ 超长时压缩（保留最近轮次+LLM 摘要）
        else:
            messages = _trim_history(messages, MAX_HISTORY_MSGS)              # ⑤' --no-compact 退化为纯硬删
    else:
        # for 循环正常走完（没有 break）说明达到了 max_steps
        if verbose:
            print(f"\n⚠️ 达到最大步数 {max_steps}，强制停止。")
        final = "（达到最大步数强制停止，任务未确认完成）"
    return final, messages


# mock 模式的"剧本"：模拟模型 3 次工具调用 + 1 句完成语，无 key 也能跑通 loop
MOCK_SCRIPT = [
    (None, [{"id": "m1", "name": "run_bash", "arguments": {"command": "dir"}}]),
    (None, [{"id": "m2", "name": "write_file",
             "arguments": {"path": "hello.py", "content": "# hello.py\nprint(\"hello from agent\")"}}]),
    (None, [{"id": "m3", "name": "run_bash", "arguments": {"command": "python hello.py"}}]),
    ("任务完成：已创建并运行 hello.py，输出 hello from agent。", None),
]


def main():
    ap = argparse.ArgumentParser(description="编程智能体：自主读写文件、执行命令完成编程任务")
    ap.add_argument("--task", help="一次性任务；不填则进入交互式对话")
    ap.add_argument("--workdir", default=".", help="agent 的工作目录（默认当前目录）")
    ap.add_argument("--max-steps", type=int, default=MAX_STEPS, help=f"最大循环步数（默认 {MAX_STEPS}，安全阀防死循环）")
    ap.add_argument("--mock", action="store_true", help="用模拟模型跑通逻辑（无需 API key）")
    ap.add_argument("--no-compact", action="store_true", help="超长时退化为硬删整轮，不做 LLM 总结压缩")
    ap.add_argument("--max-history-chars", type=int, default=MAX_HISTORY_CHARS,
                    help=f"历史字符预算，超过则触发压缩（默认 {MAX_HISTORY_CHARS}，按接入模型的上下文窗口调整）")
    ap.add_argument("--session", metavar="ID", help="恢复指定会话 ID（session/<ID>.json），在其上下文上继续")
    ap.add_argument("--resume", action="store_true", help="启动时列出历史会话，输入序号选择恢复")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")   # Windows 终端中文乱码修复
    except Exception:
        pass

    workdir = os.path.abspath(args.workdir)
    if not os.path.isdir(workdir):
        print(f"工作目录不存在: {workdir}")
        sys.exit(1)

    # 选择模型客户端：--mock 用 MockLLM（无 key），否则用真实 LLMClient
    if args.mock:
        llm = MockLLM(MOCK_SCRIPT)
        print("⚠️  mock 模式：用预设脚本模拟模型，验证 loop 逻辑（不调用真实 API）")
    else:
        try:
            llm = LLMClient()
        except LLMError as e:
            print(f"❌ {e}")
            print("   解决：设置环境变量 DEEPSEEK_API_KEY，或加 --mock 走模拟模式。")
            sys.exit(1)

    if args.task:
        # 一次性任务：可选 --session 恢复旧上下文；跑完自动保存，方便 --session 续跑
        conversation = None
        session_id = _new_session_id()
        if args.session:
            conversation = _load_session(args.session)
            if conversation is None:
                print(f"❌ 会话不存在：{args.session}")
                _print_available()
                sys.exit(1)
            session_id = args.session
            _refresh_system(conversation, workdir)
            print(f"已恢复会话 {args.session}（{len(conversation)} 条消息），在此基础上继续。")
        final, conversation = run_agent(llm, args.task, workdir, max_steps=args.max_steps,
                                        compact=not args.no_compact, messages=conversation,
                                        max_chars=args.max_history_chars)
        _save_session(session_id, conversation)
        print(f"\n✔ 任务结束，最终回复：{final}")
        print(f"会话已保存：session/{session_id}.json（下次可用 --session {session_id} 恢复继续）")
    else:
        # 交互式对话：同一终端上下文统一（跨任务累积）；exit 退出；/clear 清空；/compact 手动压缩；/resume 恢复；/loop 循环；运行中按 ESC 中断
        print(f"编程智能体已启动（工作目录: {workdir}）。")
        print("输入任务开始；exit 退出；/clear 清空会话；/compact 压缩历史；/resume [ID] 恢复会话；/loop <间隔> 任务 定时执行；任务运行中按 ESC 可中断；")
        print("启动时 --resume 或 --session <ID> 可恢复；交互中 /resume 无参列出历史会话选序号。")
        session_id = _new_session_id()
        conversation = None
        if args.session:
            conversation = _load_session(args.session)
            if conversation is None:
                print(f"❌ 会话不存在：{args.session}")
                _print_available()
                sys.exit(1)
            session_id = args.session
            _refresh_system(conversation, workdir)
            print(f"已恢复会话 {args.session}（{len(conversation)} 条消息），继续累积上下文。")
        elif args.resume:
            sid, conv = _choose_session()
            if conv is not None:
                session_id, conversation = sid, _refresh_system(conv, workdir)
                print(f"已恢复会话 {session_id}（{len(conversation)} 条消息）。")
        print(f"当前会话 ID：{session_id}（下次可用 --session {session_id} 恢复）")
        while True:
            try:
                task = _clean_text(input("\n你: ")).strip()
            except EOFError:
                break
            if not task:
                continue
            if task.lower() in ("exit", "quit"):
                break
            if task.lower() in ("/clear", "clear"):
                conversation = None
                print("已清空会话上下文，开始全新对话。")
                continue
            if task.lower() in ("/compact", "compact"):
                if conversation is None:
                    print("还没有任何对话，无需压缩。")
                    continue
                before = len(conversation)
                conversation = _compact_history(conversation, llm, force=True)
                if len(conversation) == before:
                    print("历史太短或压缩失败，未发生变化。")
                    continue
                summary = ""
                if conversation[1].get("role") == "user" and "[先前对话已压缩" in conversation[1].get("content", ""):
                    summary = conversation[1]["content"].split("\n", 1)[-1][:150]
                print(f"已手动压缩：{before} -> {len(conversation)} 条消息。")
                if summary:
                    print(f"摘要：{summary}")
                continue
            if task.lower().startswith("/resume"):
                # 交互内恢复会话：/resume <ID> 直接恢复指定 ID；/resume 无参则列出历史会话选序号。
                # 切到目标会话后 session_id 同步更新，后续任务继续写回该会话文件。
                parts = task.split(maxsplit=1)
                if len(parts) == 2:
                    sid = parts[1].strip()
                    conv = _load_session(sid)
                    if conv is None:
                        print(f"❌ 会话不存在：{sid}")
                        _print_available()
                    else:
                        conversation = _refresh_system(conv, workdir)
                        session_id = sid
                        print(f"已恢复会话 {sid}（{len(conversation)} 条消息），上下文已切换。")
                else:
                    sid, conv = _choose_session()
                    if conv is not None:
                        conversation = _refresh_system(conv, workdir)
                        session_id = sid
                        print(f"已恢复会话 {sid}（{len(conversation)} 条消息），上下文已切换。")
                continue
            if task.lower().startswith("/loop"):
                # /loop <间隔> <任务>：每隔 interval 秒自动激活 agent 执行一次任务（类似 cc 的定时 loop）。
                # 立即执行一轮，之后每间隔秒再自动执行；间隔支持 30s / 5m / 60（缺省单位=秒）。
                # 轮间 sleep 每秒检测 ESC 可提前停止；MAX_LOOP_ROUNDS 护栏防忘记停挂机。
                rest = task[5:].strip()
                parts = rest.split(maxsplit=1)
                interval = 60   # 默认 60 秒
                if parts and re.match(r"^\d+[sm]?$", parts[0]):
                    raw = parts[0]
                    if raw[-1] in "sm":
                        interval = int(raw[:-1]) * (60 if raw[-1] == "m" else 1)
                    else:
                        interval = int(raw)
                    rest = parts[1] if len(parts) > 1 else ""
                if not rest:
                    print("用法：/loop <间隔> <任务>，例如 /loop 30s 检查服务器状态、/loop 5m 汇报天气。按 ESC 停止。")
                    continue
                loop_task = rest
                rounds = 0
                print(f"⏰ /loop 已启动：每 {interval} 秒自动执行「{loop_task}」，立即开始，按 ESC 停止。")
                while True:
                    rounds += 1
                    print(f"\n─── /loop 第 {rounds} 轮（{datetime.now().strftime('%H:%M:%S')}）───")
                    _, conversation = run_agent(llm, loop_task, workdir, max_steps=args.max_steps,
                                                compact=not args.no_compact, messages=conversation,
                                                max_chars=args.max_history_chars)
                    _save_session(session_id, conversation)
                    if rounds >= MAX_LOOP_ROUNDS:
                        print(f"已到达 {MAX_LOOP_ROUNDS} 轮护栏，/loop 停止。")
                        break
                    stopped = False
                    for _ in range(interval):
                        if _interrupt_requested():
                            stopped = True
                            break
                        time.sleep(1)
                    if stopped:
                        print(f"按 ESC，/loop 已停止（共执行 {rounds} 轮）。")
                        break
                continue
            _, conversation = run_agent(llm, task, workdir, max_steps=args.max_steps,
                                        compact=not args.no_compact, messages=conversation,
                                        max_chars=args.max_history_chars)
            _save_session(session_id, conversation)
        if conversation:
            _save_session(session_id, conversation)   # 退出前兜底保存


if __name__ == "__main__":
    main()

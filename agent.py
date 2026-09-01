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
import json
import os
import subprocess
import sys

from llm import LLMClient, LLMError, MockLLM

# 两个关键常量：控制"回传给模型的内容大小"和"单条命令的执行时长"
MAX_OUTPUT = 8000      # 工具结果返回给模型的内容上限（字符），防止上下文被单条长输出塞爆
CMD_TIMEOUT = 60       # 单条命令超时（秒），防止命令无限卡住

SYSTEM_PROMPT = """你是编程智能体，负责在本地工作目录 {workdir} 中完成用户交给的编程任务。
你可以通过调用工具来操作电脑：
- run_bash：执行 shell 命令（Windows 环境，列目录用 dir；可用 python 运行/测试程序）
- read_file：读取文本文件
- write_file：写入或覆盖文本文件

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


def run_agent(llm, task, workdir, max_steps=30, verbose=True):
    """
    agent 主循环（全项目发动机）。
    流程：发历史+工具定义 → 模型返回 → 无工具调用即完成 / 有则本地执行+回填 → 循环。
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(workdir=workdir)},
        {"role": "user", "content": task},
    ]
    final = None
    for step in range(1, max_steps + 1):
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
        messages = _trim_history(messages)                      # ⑤ 超长裁剪
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
    ap.add_argument("--max-steps", type=int, default=30, help="最大循环步数")
    ap.add_argument("--mock", action="store_true", help="用模拟模型跑通逻辑（无需 API key）")
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
        final, _ = run_agent(llm, args.task, workdir, max_steps=args.max_steps)
        print(f"\n✔ 任务结束，最终回复：{final}")
    else:
        # 交互式对话：输入 exit 退出
        print(f"编程智能体已启动（工作目录: {workdir}）。输入任务开始，输入 exit 退出。")
        while True:
            try:
                task = input("\n你: ").strip()
            except EOFError:
                break
            if not task:
                continue
            if task.lower() in ("exit", "quit"):
                break
            run_agent(llm, task, workdir, max_steps=args.max_steps)


if __name__ == "__main__":
    main()

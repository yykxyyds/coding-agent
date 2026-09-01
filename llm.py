"""LLM 客户端：调用 DeepSeek（OpenAI 兼容 /chat/completions），并内置 mock 模式供无 key 自测。

只用 Python 标准库（urllib），不依赖任何 SDK。
"""
import json
import os
import urllib.request
import urllib.error

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"   # DeepSeek 接口根地址
DEFAULT_MODEL = "deepseek-chat"                    # 默认模型


class LLMError(Exception):
    """API 调用失败时抛出的自定义异常（上层捕获后给出友好提示）。"""


class LLMClient:
    """真实客户端：直连 DeepSeek，支持 tool calling。
    chat() 返回 (content, tool_calls)：
      content     : 模型最终文本回复；若本轮是工具调用则为 None
      tool_calls  : list[{"id", "name", "arguments"}]（arguments 已解析为 dict）；无则 None
    """

    def __init__(self, api_key=None, base_url=None, model=None, timeout=120):
        # key 优先用参数，否则从环境变量读——凭据绝不写进代码
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise LLMError("未提供 DEEPSEEK_API_KEY。请设置环境变量，或用 --mock 走模拟模式。")
        self.base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL)
        self.model = model or os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL)
        self.timeout = timeout   # 单次请求超时（秒）

    def chat(self, messages, tools=None):
        """一次完整对话：构造请求 → 发送 → 解析响应，返回 (content, tool_calls)。"""
        payload = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = tools   # 工具 schema 放请求体顶层，与 messages 平级

        req = urllib.request.Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),   # 请求体 → JSON 字节
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,   # 认证头（API key）
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # HTTP 错误（4xx/5xx）：带上状态码和响应体片段
            body = e.read().decode("utf-8", errors="replace")
            raise LLMError(f"API HTTP {e.code}: {body[:500]}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            # 网络层错误 / 超时：统一转成 LLMError
            raise LLMError(f"无法连接 API: {e}") from e

        # ── 模型输出解析（五个关键逻辑之一）──
        message = data["choices"][0]["message"]      # 取第一个 choice 的 message
        content = message.get("content")             # 文字回复（工具调用轮为 None）
        raw_tools = message.get("tool_calls") or []  # 工具调用列表（可能没有）
        tool_calls = []
        for tc in raw_tools:
            fn = tc.get("function", {})
            args_text = fn.get("arguments") or "{}"  # arguments 是【JSON 字符串】
            try:
                args = json.loads(args_text)         # 字符串 → dict，变成本地可执行参数
            except json.JSONDecodeError:
                # 解析失败不中断：带原始串兜底，交给执行层报错回传、让模型自纠
                args = {"_raw_arguments": args_text}
            tool_calls.append({                      # 统一成内部格式
                "id": tc.get("id"),
                "name": fn.get("name", ""),
                "arguments": args,
            })
        return content, (tool_calls or None)         # 空列表归一化为 None，对上前层终止判断


class MockLLM:
    """无 key 自测用：按预设脚本依次返回响应，验证 loop 的机械逻辑。

    script: list[(content, tool_calls)]，每次 chat() 弹出下一个。
    与 LLMClient 同接口 → run_agent 无感知切换真/假模式。
    """

    def __init__(self, script, tag="mock"):
        self._script = list(script)   # 拷贝剧本，防止外部改动
        self.tag = tag

    def chat(self, messages, tools=None):
        # 模拟"模型"：不调 API，直接从剧本里弹出下一条回复
        if not self._script:
            return "（mock 无更多响应，结束）", None
        return self._script.pop(0)

"""LLM 客户端：调用 DeepSeek（OpenAI 兼容 /chat/completions），并内置 mock 模式供无 key 自测。

只用 Python 标准库（urllib），不依赖任何 SDK。
"""
import json
import os
import urllib.request
import urllib.error

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"


class LLMError(Exception):
    """API 调用失败。"""


class LLMClient:
    """真实客户端：直连 DeepSeek，支持 tool calling。

    chat() 返回 (content, tool_calls)：
      content     : 模型最终文本回复；若本轮是工具调用则为 None
      tool_calls  : list[{"id", "name", "arguments"}]（arguments 已解析为 dict）；无则 None
    """

    def __init__(self, api_key=None, base_url=None, model=None, timeout=120):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise LLMError("未提供 DEEPSEEK_API_KEY。请设置环境变量，或用 --mock 走模拟模式。")
        self.base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL)
        self.model = model or os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL)
        self.timeout = timeout

    def chat(self, messages, tools=None):
        payload = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = tools

        req = urllib.request.Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise LLMError(f"API HTTP {e.code}: {body[:500]}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise LLMError(f"无法连接 API: {e}") from e

        message = data["choices"][0]["message"]
        content = message.get("content")
        raw_tools = message.get("tool_calls") or []
        tool_calls = []
        for tc in raw_tools:
            fn = tc.get("function", {})
            args_text = fn.get("arguments") or "{}"
            try:
                args = json.loads(args_text)
            except json.JSONDecodeError:
                # 解析失败不中断：把原始串也带上，交给上层自行处理
                args = {"_raw_arguments": args_text}
            tool_calls.append({
                "id": tc.get("id"),
                "name": fn.get("name", ""),
                "arguments": args,
            })
        return content, (tool_calls or None)


class MockLLM:
    """无 key 自测用：按预设脚本依次返回响应，验证 loop 的机械逻辑。

    script: list[(content, tool_calls)]，每次 chat() 弹出下一个。
    """

    def __init__(self, script, tag="mock"):
        self._script = list(script)
        self.tag = tag

    def chat(self, messages, tools=None):
        if not self._script:
            return "（mock 无更多响应，结束）", None
        return self._script.pop(0)

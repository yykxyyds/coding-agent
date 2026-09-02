# -*- coding: utf-8 -*-
"""compact 单元自测：构造超长历史，用 MockLLM 验证压缩/降级/边界/交互续跑。

放在 function_test/ 下，随仓库提交（功能测试）。
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import (_compact_history, _trim_history, _keep_start, _history_chars, run_agent, _interrupt_requested)
from llm import MockLLM


def make_round(i):
    """一轮 = assistant(带 tool_calls) + 1 条 tool 结果。"""
    return [
        {"role": "assistant", "content": f"第{i}步想法",
         "tool_calls": [{"id": f"t{i}", "type": "function",
                         "function": {"name": "run_bash", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": f"t{i}", "content": f"第{i}步输出"},
    ]


def history(rounds=30):
    msgs = [
        {"role": "system", "content": "你是编程智能体"},
        {"role": "user", "content": "写一个 hello.py"},
    ]
    for i in range(rounds):
        msgs += make_round(i)
    return msgs


def check_no_orphan(msgs):
    """协议：tool 消息必须紧跟其 assistant，且 tool_call_id 匹配。"""
    for i, m in enumerate(msgs):
        if m["role"] == "tool":
            assert i > 0 and msgs[i - 1]["role"] == "assistant", f"孤立 tool 消息 at {i}"
            ids = [tc["id"] for tc in msgs[i - 1].get("tool_calls", [])]
            assert m["tool_call_id"] in ids, f"tool_call_id 不匹配 at {i}"


# ── 1. 正常压缩：字符预算触发 + 摘要前置 + 不拆对 + 保留最近轮次 ──
h = history(30)
# 预算要满足：总字符(≈359) > max_chars > 保留区字符(≈130)，否则压缩结果被判"仍超限"而降级
llm = MockLLM([("【摘要】已完成任务第一步，待办：运行 hello.py。", None)])
r = _compact_history(h, llm, max_chars=200, keep_recent=10)
print(f"[1] 触发 {len(h)} 条 / {_history_chars(h)} 字符 -> {len(r)} 条 / {_history_chars(r)} 字符")
assert len(r) < len(h) and _history_chars(r) < _history_chars(h), "压缩应显著减小"
assert r[0]["role"] == "system"
assert r[1]["role"] == "user" and "[先前对话已压缩" in r[1]["content"], "摘要未前置/无边界标记"
assert "待办" in r[1]["content"], "摘要内容未保留"
check_no_orphan(r)
assert r[-1]["tool_call_id"] == "t29", "最近轮次未被保留"
print("[1] PASS 摘要前置/边界标记/不拆对/保留最近轮次")

# ── 2. _keep_start 边界：保留区第一条非 tool ──
ks = _keep_start(h, keep_recent=10)
assert ks > 1 and h[ks]["role"] != "tool"
print(f"[2] PASS keep_start={ks}，保留区首条={h[ks]['role']}")

# ── 3. 压缩失败降级：MockLLM 返回空 → _summarize None → 硬删（不产生摘要）──
h2 = history(30)
r2 = _compact_history(h2, MockLLM([("", None)]), max_chars=200, keep_recent=10)
print(f"[3] 降级 {len(h2)} 条 -> {len(r2)} 条")
assert not any("[先前对话已压缩" in m.get("content", "") for m in r2), "降级后不应有摘要消息"
check_no_orphan(r2)
print("[3] PASS 压缩失败降级，无摘要消息")

# ── 4. 未超预算不动 ──
h3 = history(5)
assert _compact_history(h3, llm, max_chars=1000, keep_recent=10) == h3
print("[4] PASS 未超预算时原样返回")

# ── 5. _trim_history 硬删对照（--no-compact 路径）──
h4 = history(30)
r4 = _trim_history(h4, max_len=50)
assert len(r4) <= 50
check_no_orphan(r4)
assert not any("[先前对话已压缩" in m.get("content", "") for m in r4)
print(f"[5] PASS _trim_history 硬删 {len(h4)} -> {len(r4)} 条，无摘要")

# ── 6/7. run_agent 集成（compact 两种模式）一步完成 ──
f6, _ = run_agent(MockLLM([("任务完成", None)]), "hello", ".", max_steps=3, verbose=False)
assert f6 == "任务完成"
f7, _ = run_agent(MockLLM([("任务完成", None)]), "hello", ".", max_steps=3, verbose=False, compact=False)
assert f7 == "任务完成"
print("[6/7] PASS run_agent(compact True/False) 正常")

# ── 8. 交互上下文统一：第二次任务带上第一次的历史，agent 记得之前做了什么 ──
_, conv = run_agent(MockLLM([("第一步完成", None)]), "任务A：写 hello.py", ".", max_steps=2, verbose=False)
assert conv[0]["role"] == "system"
_, conv2 = run_agent(MockLLM([("第二步完成", None)]), "任务B：接着验证它", ".", max_steps=2, verbose=False, messages=conv)
user_texts = [m["content"] for m in conv2 if m["role"] == "user"]
assert "任务A：写 hello.py" in user_texts and "任务B：接着验证它" in user_texts, "交互续跑未保留前序任务上下文"
assert conv2[0]["role"] == "system" and conv2[1]["role"] == "user"
print(f"[8] PASS 交互上下文统一：{len(conv)} -> {len(conv2)} 条，含两次任务的 user 消息")

# ── 9. 手动压缩（/compact 的 force=True）：预算未超也强制压缩 ──
h9 = history(30)  # 2005 字符 < 默认 20 万预算，自动模式不会触发
r9 = _compact_history(h9, MockLLM([("【摘要】已完成分析，待办：写报告。", None)]), force=True)
assert "[先前对话已压缩" in r9[1]["content"], "force 模式应跳过预算检查强制压缩"
assert len(r9) < len(h9)
check_no_orphan(r9)
print(f"[9] PASS force 手动压缩 {len(h9)} -> {len(r9)} 条（预算未超也压缩）")

# ── 10. 手动压缩但历史太短：force 应原样返回，不删内容 ──
h10 = history(0)  # 仅 system + user
r10 = _compact_history(h10, MockLLM([("摘要", None)]), force=True)
assert r10 == h10, "历史太短时 force 压缩不应改动消息"
print("[10] PASS 历史太短时 force 原样返回")

# ── 11. _interrupt_requested：无按键时返回 False ──
assert _interrupt_requested() is False
print("[11] PASS _interrupt_requested 无按键返回 False")

print("\n全部断言通过")

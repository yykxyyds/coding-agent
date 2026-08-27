"""自检脚本：无 API key 时验证 agent 的核心逻辑（工具、loop、上下文管理、错误处理）。

用法：在 code/ 目录下运行  python -u self_test.py
"""
import os
import sys
import tempfile
import traceback

sys.stdout.reconfigure(encoding="utf-8")

from agent import (
    _trim_history, _safe_path, tool_run_bash, tool_read_file,
    tool_write_file, execute_tool, run_agent,
)
from llm import MockLLM

CORRECTED = (
    "def add(a, b):\n"
    "    return a + b\n"
    "\n"
    "if __name__ == '__main__':\n"
    "    print(add(2, 3))\n"
)
BUGGY = CORRECTED.replace("return a + b", "return a - b")

PASS = 0
FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✔ {name}")
    else:
        FAIL += 1
        print(f"  ✘ {name} {extra}")


# ---------- 1. 工具函数 ----------
print("[1] 工具函数")
tmp = tempfile.mkdtemp(prefix="agent_selftest_")

check("run_bash 基本执行", tool_run_bash('python -c "print(1+1)"', tmp).strip() == "2")

wp = os.path.join(tmp, "hello.txt")
check("write_file 写入", "已写入" in tool_write_file("hello.txt", "hello 世界", tmp))
check("read_file 读回", tool_read_file("hello.txt", tmp) == "hello 世界")

check("越界路径被拒绝", tool_read_file("../secret.txt", tmp).startswith("[错误] 路径越界"))
check("未知工具报错", execute_tool("rm -rf", {}, tmp).startswith("[错误] 未知工具"))

# ---------- 2. 上下文管理 ----------
print("[2] 上下文管理 _trim_history")
msgs = [{"role": "system", "content": "sys"}]
for i in range(40):
    msgs.append({"role": "assistant", "content": None, "tool_calls": [{"id": f"c{i}"}]})
    msgs.append({"role": "tool", "tool_call_id": f"c{i}", "content": f"r{i}"})
trimmed = _trim_history(list(msgs), max_len=50)
check("截断后条数不超限", len(trimmed) <= 50)
roles = [m["role"] for m in trimmed]
check("无孤立 tool 消息", "tool" not in roles or roles[roles.index("tool") - 1] == "assistant")
check("system 保留在开头", trimmed[0]["role"] == "system")

# ---------- 3. mock 端到端 loop（模拟"修 bug"） ----------
print("[3] mock 端到端 loop")
script = [
    (None, [{"id": "t1", "name": "run_bash", "arguments": {"command": "python mathy.py"}}]),
    (None, [{"id": "t2", "name": "read_file", "arguments": {"path": "mathy.py"}}]),
    (None, [{"id": "t3", "name": "write_file",
             "arguments": {"path": "mathy.py", "content": CORRECTED}}]),
    (None, [{"id": "t4", "name": "run_bash", "arguments": {"command": "python mathy.py"}}]),
    ("修复完成，add(2,3)=5。", None),
]
with open(os.path.join(tmp, "mathy.py"), "w", encoding="utf-8") as f:
    f.write(BUGGY)

final, msgs = run_agent(MockLLM(script), "帮我修复 mathy.py 的 bug", tmp, max_steps=20, verbose=False)
check("loop 正常终止并给出总结", "修复完成" in final)
with open(os.path.join(tmp, "mathy.py"), encoding="utf-8") as f:
    content = f.read()
check("文件被工具真实修改", content == CORRECTED)

# ---------- 4. 最大步数保护 ----------
print("[4] 最大步数保护")
loop_script = [(None, [{"id": f"l{i}", "name": "run_bash", "arguments": {"command": "echo x"}}]) for i in range(100)]
final2, _ = run_agent(MockLLM(loop_script), "test", tmp, max_steps=5, verbose=False)
check("超步数强制停止", "强制停止" in final2)

print(f"\n结果: {PASS} 通过, {FAIL} 失败")
sys.exit(1 if FAIL else 0)

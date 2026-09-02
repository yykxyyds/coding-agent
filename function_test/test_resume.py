# -*- coding: utf-8 -*-
"""resume 会话持久化自测：ID 生成、保存/加载往返、列表排序、system 重建、跨会话续跑。

放在 function_test/ 下，随仓库提交（功能测试）。
"""
import os
import re
import shutil
import sys
import tempfile
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent as agent_mod
from agent import (_new_session_id, _save_session, _load_session, _list_sessions,
                   _refresh_system, _first_task, run_agent, SYSTEM_PROMPT, SESSION_DIR)
from llm import MockLLM

WD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_wd")
os.makedirs(WD, exist_ok=True)

# ── 1. 会话 ID 格式（时间戳）──
sid = _new_session_id()
assert re.fullmatch(r"\d{8}-\d{6}", sid), sid
print(f"[1] PASS 会话 ID = {sid}")

# ── 2. 保存/加载往返 + 列表（统一存到项目根 session/，不随 workdir 变）──
msgs = [{"role": "system", "content": SYSTEM_PROMPT.format(workdir=WD)},
        {"role": "user", "content": "任务A：写 hello.py"}]
_save_session(sid, msgs)
assert sid in _list_sessions(), "列表应包含刚保存的会话"
loaded = _load_session(sid)
assert loaded == msgs, "加载应与保存一致"
assert _list_sessions() == sorted(_list_sessions(), reverse=True), "列表应最新在前"
assert os.path.isfile(os.path.join(SESSION_DIR, f"{sid}.json")), "应存到项目根 session/"
assert not os.path.isfile(os.path.join(WD, "session", f"{sid}.json")), "不应存到 workdir 下的 session"
print(f"[2] PASS 保存/加载往返，列表共 {len(_list_sessions())} 个会话，目录={os.path.relpath(SESSION_DIR)}")

# ── 3. system 重建（恢复时用当前 workdir）──
other = os.path.normpath(os.path.join(WD, "..", "other_wd"))
_refresh_system(loaded, other)
assert loaded[0]["content"] == SYSTEM_PROMPT.format(workdir=other), "system 应重建为当前 workdir"
print("[3] PASS _refresh_system 重建 system")

# ── 4. _first_task 取首个用户任务 ──
assert _first_task(msgs) == "任务A：写 hello.py"
print("[4] PASS _first_task")

# ── 5. run_agent 跨会话续跑：任务A 保存 → 恢复 → 任务B，两个 user 任务都在 ──
_, conv_a = run_agent(MockLLM([("第一步完成", None)]), "任务A：写 hello.py", WD, max_steps=2, verbose=False)
_save_session(sid, conv_a)
conv_r = _load_session(sid)
assert conv_r is not None
_, conv_b = run_agent(MockLLM([("第二步完成", None)]), "任务B：接着验证它", WD, max_steps=2, verbose=False, messages=conv_r)
users = [m["content"] for m in conv_b if m["role"] == "user"]
assert "任务A：写 hello.py" in users and "任务B：接着验证它" in users, "续跑应保留前序任务上下文"
assert conv_b[0]["role"] == "system"
print(f"[5] PASS 跨会话续跑：{len(conv_a)} 条 → 恢复 → {len(conv_b)} 条，含任务A和任务B")

# ── 6. 无会话目录时 _choose_session 返回 (None, None)（临时替换 SESSION_DIR 到空目录）──
tmp = tempfile.mkdtemp()
orig_dir = agent_mod.SESSION_DIR
try:
    agent_mod.SESSION_DIR = tmp
    assert agent_mod._choose_session() == (None, None)
finally:
    agent_mod.SESSION_DIR = orig_dir
shutil.rmtree(tmp, ignore_errors=True)
print("[6] PASS 无会话时 _choose_session 返回 (None, None)")

# 清理测试会话文件，保持目录整洁
p = os.path.join(SESSION_DIR, f"{sid}.json")
if os.path.isfile(p):
    os.remove(p)
print("\n全部断言通过")

#!/usr/bin/env python3
"""测试脚本：自动化验证 todo.py 的 add / list / done / remove 四个功能。

通过 subprocess 以独立进程运行 todo.py，并对输出做断言。
测试使用独立的临时数据文件，避免污染真实数据。
"""

import json
import os
import subprocess
import sys
import tempfile

# 让 todo.py 使用临时数据文件进行测试
TEST_DIR = tempfile.mkdtemp(prefix="todo_test_")
TEST_DATA = os.path.join(TEST_DIR, "todo.json")
os.environ["TODO_DATA_FILE"] = TEST_DATA

# 修改 todo.py 使其支持通过环境变量指定数据文件（便于测试隔离）
_todo_code = open("todo.py", encoding="utf-8").read().replace(
    'DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json")',
    'DATA_FILE = os.environ.get("TODO_DATA_FILE", ' +
    'os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json"))'
)
_todo_path = os.path.join(TEST_DIR, "todo_under_test.py")
open(_todo_path, "w", encoding="utf-8").write(_todo_code)

passed = 0
failed = 0


def run_todo(*args):
    """运行被测试的 todo.py 并返回 (returncode, stdout, stderr)。"""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, _todo_path, *args],
        capture_output=True, text=True, encoding="utf-8", env=env
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"[PASS] {name}")
    else:
        failed += 1
        print(f"[FAIL] {name}  {detail}")


def read_data():
    """读取测试数据文件。"""
    with open(TEST_DATA, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # 清理可能残留的测试数据
    if os.path.exists(TEST_DATA):
        os.remove(TEST_DATA)

    # ---------- 1. add（添加） ----------
    rc, out, err = run_todo("add", "买牛奶")
    check("add 返回码为 0", rc == 0, f"rc={rc}, err={err}")
    check("add 输出包含内容", "买牛奶" in out, out)

    run_todo("add", "写周报")
    run_todo("add", "锻炼身体")
    data = read_data()
    check("add 创建 3 条待办", len(data) == 3, str(data))
    check("新待办未完成", all(not t["done"] for t in data), str(data))
    check("id 依次递增", [t["id"] for t in data] == [1, 2, 3], str(data))
    check("内容正确", [t["content"] for t in data] == ["买牛奶", "写周报", "锻炼身体"], str(data))

    # ---------- 2. list（列出） ----------
    rc, out, err = run_todo("list")
    check("list 返回码为 0", rc == 0, f"rc={rc}, err={err}")
    check("list 显示 3 条", out.count("#") == 3, out)
    check("list 显示未完成符号", "[ ]" in out, out)
    check("list 包含各内容", all(c in out for c in ["买牛奶", "写周报", "锻炼身体"]), out)

    # ---------- 3. done（标记完成） ----------
    rc, out, err = run_todo("done", "2")
    check("done 返回码为 0", rc == 0, f"rc={rc}, err={err}")
    check("done 输出提示", "已标记完成" in out, out)
    data = read_data()
    done_states = [t["done"] for t in data]
    check("第2条已完成", done_states == [False, True, False], str(data))

    rc, out, _ = run_todo("list")
    check("list 显示完成符号", "[x] #2" in out, out)

    # 重复标记 done 的容错
    rc, out, _ = run_todo("done", "2")
    check("重复 done 友好提示", "无需重复" in out, out)

    # ---------- 4. remove（删除） ----------
    rc, out, err = run_todo("remove", "1")
    check("remove 返回码为 0", rc == 0, f"rc={rc}, err={err}")
    check("remove 输出提示", "已删除" in out, out)
    data = read_data()
    check("删除后剩 2 条", len(data) == 2, str(data))
    check("被删内容不存在", "买牛奶" not in [t["content"] for t in data], str(data))
    check("删除后 id 重新连续", [t["id"] for t in data] == [1, 2], str(data))
    check("剩余内容正确", [t["content"] for t in data] == ["写周报", "锻炼身体"], str(data))
    check("已完成状态保留", data[0]["done"] is True, str(data))

    # remove 不存在的 id 的容错
    rc, out, _ = run_todo("remove", "99")
    check("remove 不存在的 id 提示错误", "找不到" in out, out)

    # ---------- 汇总 ----------
    print(f"\n结果：{passed} 通过，{failed} 失败")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

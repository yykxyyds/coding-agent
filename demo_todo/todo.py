#!/usr/bin/env python3
"""一个简单的命令行待办事项工具。

数据保存到本地文件（默认 todo.json），支持：
    add    添加待办       todo.py add "买牛奶"
    list   列出待办       todo.py list
    done   标记完成       todo.py done 1
    remove 删除待办       todo.py remove 1

用法：
    python todo.py add <内容>
    python todo.py list
    python todo.py done <编号>
    python todo.py remove <编号>
"""

import json
import os
import sys

# 数据文件默认存放位置：与脚本同目录下的 todo.json
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json")


def load_todos():
    """从数据文件加载待办列表；文件不存在或损坏时返回空列表。"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def save_todos(todos):
    """把待办列表写回数据文件。"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def add_todo(content):
    """添加一条待办，返回新待办信息。"""
    content = content.strip()
    if not content:
        print("错误：待办内容不能为空。")
        return
    todos = load_todos()
    todo = {"id": len(todos) + 1, "content": content, "done": False}
    todos.append(todo)
    save_todos(todos)
    print(f"已添加：#{todo['id']} {content}")


def list_todos():
    """列出所有待办。"""
    todos = load_todos()
    if not todos:
        print("暂无待办事项。")
        return
    print("待办事项列表：")
    for todo in todos:
        status = "[x]" if todo["done"] else "[ ]"
        print(f"  {status} #{todo['id']}: {todo['content']}")


def _find_todo(todo_id):
    """按 id 查找待办，返回 (index, todo)；找不到返回 (None, None)。"""
    todos = load_todos()
    for i, todo in enumerate(todos):
        if todo["id"] == todo_id:
            return i, todo
    return None, None


def mark_done(todo_id):
    """把指定 id 的待办标记为完成。"""
    todos = load_todos()
    index, todo = _find_todo(todo_id)
    if todo is None:
        print(f"错误：找不到编号为 {todo_id} 的待办。")
        return
    if todo["done"]:
        print(f"#{todo_id} 已完成，无需重复标记。")
        return
    todo["done"] = True
    todos[index] = todo
    save_todos(todos)
    print(f"已标记完成：#{todo_id} {todo['content']}")


def remove_todo(todo_id):
    """删除指定 id 的待办。"""
    todos = load_todos()
    index, todo = _find_todo(todo_id)
    if todo is None:
        print(f"错误：找不到编号为 {todo_id} 的待办。")
        return
    removed = todos.pop(index)
    # 重新整理 id，保持连续
    for i, t in enumerate(todos, start=1):
        t["id"] = i
    save_todos(todos)
    print(f"已删除：#{removed['id']} {removed['content']}")


def print_usage():
    print(__doc__)


def main(argv):
    if not argv:
        print_usage()
        return 0

    command = argv[0]
    args = argv[1:]

    if command == "add":
        if not args:
            print("用法：python todo.py add <内容>")
            return 1
        add_todo(" ".join(args))
    elif command == "list":
        list_todos()
    elif command == "done":
        if not args:
            print("用法：python todo.py done <编号>")
            return 1
        mark_done(int(args[0]))
    elif command == "remove":
        if not args:
            print("用法：python todo.py remove <编号>")
            return 1
        remove_todo(int(args[0]))
    else:
        print(f"未知命令：{command}")
        print_usage()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

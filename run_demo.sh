#!/usr/bin/env bash
# 一键真实演示：重置 bug → 运行 agent 修复（Git Bash 用）
cd "$(dirname "$0")"
export DEEPSEEK_API_KEY="$(cat "../DeepSeekAPI.txt")"
python -c "import io;s=open('demo_bugs/counter.py',encoding='utf-8').read().replace('word_counts[w] += 1','word_counts[w] = 1');open('demo_bugs/counter.py','w',encoding='utf-8').write(s)"
echo "[1/2] 已重置 counter.py 为 bug 版，启动真实演示..."
echo "[2/2] 下方将逐行打印 agent 干活过程"
python -u agent.py --workdir . --max-steps 30 --task "demo_bugs/counter.py 这个程序运行结果不对，帮我找到 bug 并修复"

#!/usr/bin/env bash
# 一键真实演示：agent 自主读取 Excel 数据、计算指标、输出分析报告（Git Bash 用）
cd "$(dirname "$0")"
export DEEPSEEK_API_KEY="$(cat "../DeepSeekAPI.txt")"
echo "[1/2] 启动真实演示：Excel 数据分析..."
echo "[2/2] agent 将自主读取 240 行成绩数据、计算指标、分组对比、输出分析报告"
python -u agent.py --workdir . --max-steps 40 --task "请分析 demo_analysis/class_scores.xlsx 学生成绩数据：1.检查数据概览；2.计算语文数学英语的平均分最高最低及格率优秀率；3.算总分并给出总分前10和单科前5；4.按班级和性别分组统计各科平均分并给出观察结论；5.整理成中文报告保存到 demo_analysis/analysis_report.txt。可用 pandas/openpyxl。提示：Windows 上 python -c 输出中文易乱码，建议写脚本文件再运行。只允许修改 demo_analysis 目录。"

@echo off
cd /d "%~dp0"
for /f "usebackq delims=" %%k in ("..\DeepSeekAPI.txt") do set "DEEPSEEK_API_KEY=%%k"
python -u agent.py --workdir . --max-steps 40 --task "请分析 demo_analysis/class_scores.xlsx 学生成绩数据：1.检查数据概览；2.计算语文数学英语的平均分最高最低及格率优秀率；3.算总分并给出总分前10和单科前5；4.按班级和性别分组统计各科平均分并给出观察结论；5.整理成中文报告保存到 demo_analysis/analysis_report.txt。可用 pandas/openpyxl。提示：Windows 上 python -c 输出中文易乱码，建议写脚本文件再运行。只允许修改 demo_analysis 目录。"
pause

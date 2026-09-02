@echo off
cd /d "%~dp0"
for /f "usebackq delims=" %%k in ("..\DeepSeekAPI.txt") do set "DEEPSEEK_API_KEY=%%k"
python -u agent.py --workdir task_test\task1_analysis --max-steps 40 --task "学生成绩数据分析任务：
1.检查数据概览；
2.计算语文数学英语的平均分最高最低及格率优秀率；
3.算总分并给出总分前10和单科前5；
4.按班级和性别分组统计各科平均分并给出观察结论；
5.整理成中文报告，得到analysis_report.txt。"
pause

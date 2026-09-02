@echo off
cd /d "%~dp0"
for /f "usebackq delims=" %%k in ("..\DeepSeekAPI.txt") do set "DEEPSEEK_API_KEY=%%k"
rem 演示前清理：目标工作目录只保留表格文件
if exist "task_test\task1_analysis\analyze.py" del /q "task_test\task1_analysis\analyze.py"
if exist "task_test\task1_analysis\analysis_report.txt" del /q "task_test\task1_analysis\analysis_report.txt"
if exist "task_test\task1_analysis\build" rmdir /s /q "task_test\task1_analysis\build"
python -u agent.py --workdir task_test\task1_analysis --max-steps 40 --task "学生成绩数据分析任务：
1.检查数据概览；
2.计算语文数学英语的平均分最高最低及格率优秀率；
3.算总分并给出总分前10和单科前5；
4.按班级和性别分组统计各科平均分并给出观察结论；
5.整理成中文报告，得到analysis_report.txt。"
pause

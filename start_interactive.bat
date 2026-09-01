@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Coding Agent Interactive
for /f "usebackq delims=" %%k in ("..\DeepSeekAPI.txt") do set "DEEPSEEK_API_KEY=%%k"
if "%DEEPSEEK_API_KEY%"=="" (
    echo [ERROR] ..\DeepSeekAPI.txt not found or empty
    echo Please create the file with your DeepSeek API key.
    pause
    exit /b 1
)
echo Starting coding agent in interactive mode...
echo Type a task, or "exit" to quit.
python -u agent.py --workdir .
pause

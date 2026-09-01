@echo off
chcp 65001 >nul
title 贪吃蛇游戏
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3 并加入环境变量。
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

start "" python snake.py
exit /b

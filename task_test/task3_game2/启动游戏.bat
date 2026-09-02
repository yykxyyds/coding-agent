@echo off
chcp 65001 >nul
title 植物大战僵尸 Demo
cd /d "%~dp0"

echo.
echo  植物大战僵尸 Demo 正在启动...
echo  请稍候（若弹窗提示选择Python请点允许运行）
echo.

python pvz_demo.py

if errorlevel 1 (
    echo.
    echo  [错误] 启动失败，请确认已安装 Python 3 并已加入系统 PATH。
    echo  若未安装，请到 https://www.python.org/downloads/ 下载安装。
    echo.
    pause
)

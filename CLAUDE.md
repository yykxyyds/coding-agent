# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目是什么

一个最小可用的**编程智能体（coding agent）**，为南大软件学院预推免考核而写。核心是 agent loop：把"对话历史 + 工具定义"发给 DeepSeek → 解析 tool_calls → 本地执行工具 → 结果回填 → 循环，直到模型不再请求工具即视为完成。**零第三方依赖**（urllib 直连 DeepSeek 的 OpenAI 兼容接口），考核约束（双盲、保密、凭据安全）见项目根目录的 CLAUDE.md。

## 常用命令

```bash
# 自检（无需 API key，验证工具 / loop / 上下文管理 / 终止条件，11 项断言）
python -u self_test.py

# 语法检查
python -m py_compile agent.py llm.py

# 模拟模式演示（无需 key，MOCK_SCRIPT 演示修 bug）
python -u agent.py --mock --workdir . --task "demo_bugs/counter.py 运行结果不对，帮我修复"

# 真实模式（需 DEEPSEEK_API_KEY）
set/export DEEPSEEK_API_KEY=<key>     # 从项目根目录 DeepSeekAPI.txt 读取
python -u agent.py --workdir . --task "你的任务"     # 一次性任务
python -u agent.py --workdir .                       # 交互式对话，exit 退出

# 一键真实演示（自动读 key、重置 demo bug、跑 agent）
run_demo.bat      # Windows 双击
bash run_demo.sh  # Git Bash

# 一键联网调研报告演示
run_report_demo.bat
bash run_report_demo.sh

# 一键 Excel 数据分析演示（240 行成绩，agent 自主算指标+分组对比+写报告）
run_analysis_demo.bat
bash run_analysis_demo.sh
```

## 架构

- `llm.py`：LLM 客户端。`LLMClient` 用 `urllib` 调 `POST /v1/chat/completions`，返回 `(content, tool_calls)`（tool_calls 的 arguments 已 JSON 解析，解析失败不中断）；`MockLLM` 按预设脚本返回响应，供无 key 自测。
- `agent.py`：
  - `TOOLS`：3 个工具的 JSON schema（run_bash / read_file / write_file），通过 messages 发给模型
  - 工具执行：`tool_run_bash`（`_decode_bytes` 兼容 Windows 的 GBK/UTF-8 输出，`CMD_TIMEOUT` 超时兜底）、`tool_read_file` / `tool_write_file`（`_safe_path` 限制在工作目录内、`MAX_OUTPUT` 截断长结果）
  - `_trim_history`：上下文管理，超长时删最早一整轮（assistant 带 tool_calls + 其 tool 结果），保证不产生孤立的 tool 消息
  - `run_agent`：loop 主循环。协议要求先把 assistant 消息（含 tool_calls）放入历史，再 append 各 tool 结果；无 tool_calls 即终止；`max_steps` 强制停止
  - `main`：CLI（`--task` 一次性 / 无则交互；`--mock`；`--workdir`；`--max-steps`）
- `web_fetch.py` / `html_to_pdf.py`：辅助命令（联网搜索/抓网页净化正文、HTML→PDF 调 Edge headless），供 agent 通过 run_bash 组合调用，不新增工具

## 关键设计点（面试答辩素材）

- 五个"重要逻辑"全部自写：对话历史与上下文管理、工具的定义与本地执行、模型输出解析、循环终止条件、错误处理。
- 工具调用失败/未知工具：错误作为 tool 结果回传模型，模型会自行调整策略（真实演示中模型请求不存在的 edit_file 被拒后，改用 write_file 重写）。
- API key 只从环境变量 `DEEPSEEK_API_KEY` 读取，代码不含任何凭据。项目根目录的 `DeepSeekAPI.txt` 是敏感文件，勿提交进仓库。

## 演示场景

- `demo_bugs/`：修 bug（单词统计程序 counter.py，`run_demo.bat` 每次运行前会把它重置回 bug 版）
- `demo_excel/`：Excel 平均分（class_scores.xlsx，agent 用 pandas 读取计算）
- `demo_todo/`：从零写待办工具 + 测试（todo.py / test_todo.py，agent 自主生成）
- `demo_report/`：联网调研报告（agent 自主搜索+抓官方文档→提炼表格→生成 PDF；零第三方依赖）
- `demo_analysis/`：Excel 数据分析（`class_scores.xlsx` 240 行成绩，agent 用 pandas 算平均/最高/及格率、总分前10、按班级性别分组对比，输出中文报告 `analysis_report.txt`；`run_analysis_demo.bat` 一键运行，`--max-steps 40`，任务描述含 Windows 编码提示）

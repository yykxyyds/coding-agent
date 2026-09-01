# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目是什么

一个最小可用的**编程智能体（coding agent）**，为南大软件学院预推免考核而写。核心是 agent loop：把"对话历史 + 工具定义"发给 DeepSeek → 解析 tool_calls → 本地执行工具 → 结果回填 → 循环，直到模型不再请求工具即视为完成。**零第三方依赖**（urllib 直连 DeepSeek 的 OpenAI 兼容接口），考核约束（双盲、保密、凭据安全）见项目根目录的 CLAUDE.md。

## 常用命令

```bash
# 语法检查
python -m py_compile agent.py llm.py

# 模拟模式演示（无需 key，MOCK_SCRIPT 演示"写文件→运行→验证"流程）
python -u agent.py --mock --workdir . --task "写一个 hello.py 并运行它"

# 真实模式（需 DEEPSEEK_API_KEY）
set/export DEEPSEEK_API_KEY=<key>     # 从项目根目录 DeepSeekAPI.txt 读取
python -u agent.py --workdir . --task "你的任务"     # 一次性任务
python -u agent.py --workdir .                       # 交互式对话，exit 退出

# 一键 Excel 数据分析演示（240 行成绩，agent 自主算指标+分组对比+写报告）
run_analysis_demo.bat      # Windows 双击

# 一键交互式对话（自动从根目录 ..\DeepSeekAPI.txt 读 key，无需手动设环境变量）
start_interactive.bat      # Windows 双击
```

## 架构

- `llm.py`：LLM 客户端。`LLMClient` 用 `urllib` 调 `POST /v1/chat/completions`，返回 `(content, tool_calls)`（tool_calls 的 arguments 已 JSON 解析，解析失败不中断）；`MockLLM` 按预设脚本返回响应，供无 key 自测。
- `agent.py`：
  - `TOOLS`：3 个工具的 JSON schema（run_bash / read_file / write_file），通过 messages 发给模型
  - 工具执行：`tool_run_bash`（`_decode_bytes` 兼容 Windows 的 GBK/UTF-8 输出，`CMD_TIMEOUT` 超时兜底）、`tool_read_file` / `tool_write_file`（`_safe_path` 限制在工作目录内、`MAX_OUTPUT` 截断长结果）
  - `_trim_history`：上下文管理，超长时删最早一整轮（assistant 带 tool_calls + 其 tool 结果），保证不产生孤立的 tool 消息
  - `run_agent`：loop 主循环。协议要求先把 assistant 消息（含 tool_calls）放入历史，再 append 各 tool 结果；无 tool_calls 即终止；`max_steps` 强制停止
  - `main`：CLI（`--task` 一次性 / 无则交互；`--mock`；`--workdir`；`--max-steps`）

## 关键设计点（面试答辩素材）

- 五个"重要逻辑"全部自写：对话历史与上下文管理、工具的定义与本地执行、模型输出解析、循环终止条件、错误处理。
- 工具调用失败/未知工具：错误作为 tool 结果回传模型，模型会自行调整策略（真实演示中模型请求不存在的 edit_file 被拒后，改用 write_file 重写）。
- API key 只从环境变量 `DEEPSEEK_API_KEY` 读取，代码不含任何凭据。项目根目录的 `DeepSeekAPI.txt` 是敏感文件，勿提交进仓库。

## 演示场景

- `demo_analysis/`：Excel 数据分析（`class_scores.xlsx` 240 行成绩，agent 用 pandas 算平均/最高/及格率、总分前10、按班级性别分组对比，输出中文报告 `analysis_report.txt`；`run_analysis_demo.bat` 一键运行，`--max-steps 40`，任务描述含 Windows 编码提示；bat 为 GBK 编码，自动从 `..\DeepSeekAPI.txt` 读 key，不会自动清理上次的 analyze.py / analysis_report.txt）
- `demo_game/`：贪吃蛇游戏（`snake.py`，tkinter 实现、零第三方依赖，无需 API key）。`启动贪吃蛇.bat` 或 `python -u demo_game/snake.py` 直接运行

## 提交规范（公开仓库交付物）

- 仓库须公开（https://github.com/yykxyyds/coding-agent），保留完整提交历史，不压缩不改写，截止后不再推送。
- 提交信息沿用现有前缀：`feat` / `docs` / `demo` / `chore` / `test`。
- 严禁入库：API key、`DeepSeekAPI.txt`（在仓库目录之外，勿复制进来）、任何含姓名/院校的文件（双盲）。
- 提交前 `git status` 确认无敏感文件混入；`.idea/` 等 IDE 产物不入库。

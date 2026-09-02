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
python -u agent.py --workdir . --task "你的任务"     # 一次性任务（历史超长默认 LLM 总结压缩，保留最近轮次）
python -u agent.py --workdir . --task "你的任务" --no-compact   # 退化为硬删整轮，不做总结压缩
python -u agent.py --workdir . --task "你的任务" --max-history-chars 500000   # 按模型上下文窗口调字符预算
python -u agent.py --workdir .                       # 交互式对话：上下文统一跨任务累积；exit 退出；/clear 清空；/compact 手动压缩；/resume [ID] 恢复；/loop <间隔> 任务 定时执行（30s/5m，间隔秒自动激活，ESC 停）；运行中按 ESC 中断
python -u agent.py --workdir . --resume              # 交互启动时列出历史会话（session/），输入序号选择恢复
python -u agent.py --workdir . --session <ID>        # 直接恢复指定会话 ID，接着上次进度继续

# 一键 Excel 数据分析演示（240 行成绩，agent 自主算指标+分组对比+写报告）
run_task1_analysis.bat     # Windows 双击

# 一键交互式对话（自动从根目录 ..\DeepSeekAPI.txt 读 key，无需手动设环境变量）
run_interactive.bat        # Windows 双击
```

## 架构

- `llm.py`：LLM 客户端。`LLMClient` 用 `urllib` 调 `POST /v1/chat/completions`，返回 `(content, tool_calls)`（tool_calls 的 arguments 已 JSON 解析，解析失败不中断）；`MockLLM` 按预设脚本返回响应，供无 key 自测。
- `agent.py`：
  - `TOOLS`：5 个工具的 JSON schema（run_bash / read_file / write_file / web_search / web_fetch），通过 messages 发给模型
  - 工具执行：`tool_run_bash`（`_decode_bytes` 兼容 Windows 的 GBK/UTF-8 输出，`CMD_TIMEOUT` 超时兜底）、`tool_read_file` / `tool_write_file`（`_safe_path` 限制在工作目录内、`MAX_OUTPUT` 截断长结果）、`tool_web_search` / `tool_web_fetch`（纯标准库联网：urllib + Bing RSS 端点返回真实 URL 与摘要；`_decode_http` 按 UTF-8/GBK 试解、`_html_to_text` 提取正文、JS 动态渲染空页给出明确提示，`WEB_TIMEOUT`/`WEB_MAX_CHARS` 兜底）
  - `_compact_history` / `_trim_history`：上下文管理。自动触发依据是**内容字符量**而非消息条数（无 token 库，用字符近似 token 占用）——历史总字符超 `MAX_HISTORY_CHARS`（默认 20 万，可经 `--max-history-chars` 覆盖）或条数超 `MAX_HISTORY_MSGS` 护栏时压缩；`force=True` 跳过预算检查，供交互 `/compact` 手动压缩。两者都保留最近 `keep_recent` 个完整轮次原样，更老历史交给模型总结成摘要，摘要作为带边界标记的 user 消息前置到 system 之后；压缩失败/结果仍超限时自动模式降级为 `_trim_history` 硬删兜底、手动模式原样返回。都以"完整轮"为删除/压缩单元，保证不拆散 assistant 的 tool_calls 与其 tool 结果
  - `_interrupt_requested`：ESC 中断检测（Windows `msvcrt`，非 Windows 恒 False）。`run_agent` 每步开始前调用，按 ESC 即中止本轮任务、保留已累积的会话消息供继续交互
  - 会话持久化（resume）：`_save_session`/`_load_session`/`_list_sessions`/`_choose_session`/`_refresh_system`——每个终端会话用时间戳 ID，任务结束自动把对话历史存到 `<workdir>/session/<id>.json`（ASCII 转义，任何字符可安全落盘，session/ 已被 .gitignore 忽略）；`--resume` 列出历史会话选择恢复，`--session <ID>` 直接恢复续跑；交互中随时 `/resume <ID>` 切换会话（无参则列出选序号），session_id 同步更新、后续任务继续写回该会话；`_refresh_system` 把 system 重建为当前工作目录；`_clean_text` 剔除 input 里的孤立代理字符（Windows 终端/管道编码错配的防御；错配造成的中文乱码靠 chcp 65001 统一 UTF-8 避免）
  - `run_agent`：loop 主循环。协议要求先把 assistant 消息（含 tool_calls）放入历史，再 append 各 tool 结果；无 tool_calls 即终止；`max_steps`（默认 200，安全阀防死循环）强制停止。支持 `messages` 续跑参数——传入已有会话则追加新任务继续（交互模式靠它实现"一个终端上下文统一，跨任务累积"），返回的 messages 供下次续跑
  - `main`：CLI（`--task` 一次性 / 无则交互；`--mock`；`--workdir`；`--max-steps`；`--resume`；`--session`）

## 关键设计点（面试答辩素材）

- 五个"重要逻辑"全部自写：对话历史与上下文管理、工具的定义与本地执行、模型输出解析、循环终止条件、错误处理。
- 工具调用失败/未知工具：错误作为 tool 结果回传模型，模型会自行调整策略（真实演示中模型请求不存在的 edit_file 被拒后，改用 write_file 重写）。
- API key 只从环境变量 `DEEPSEEK_API_KEY` 读取，代码不含任何凭据。项目根目录的 `DeepSeekAPI.txt` 是敏感文件，勿提交进仓库。

## 演示场景（task_test/ 按任务组织）

- `task_test/task1_analysis/`：Excel 数据分析（`class_scores.xlsx` 240 行成绩，agent 用 pandas 算平均/最高/及格率、总分前10、按班级性别分组对比，输出中文报告 `analysis_report.txt`；`run_task1_analysis.bat` 一键运行，`--workdir task_test/task1_analysis` + `--max-steps 40`，任务描述含 Windows 编码提示；bat 为 GBK 编码，自动从 `..\DeepSeekAPI.txt` 读 key，运行前自动清理上次的 analyze.py / analysis_report.txt / build，工作目录仅保留表格文件，agent 从零开始）
- `task_test/task2_game/`：贪吃蛇游戏（`snake.py`，tkinter 实现、零第三方依赖，无需 API key）。`启动贪吃蛇.bat` 或 `python -u task_test/task2_game/snake.py` 直接运行
- `task_test/task3_game2/`：植物大战僵尸精简复刻（`pvz_demo.py`，tkinter 实现、零第三方依赖；目录内含开发调试日志，仅作过程展示）。`启动游戏.bat` 或 `python -u task_test/task3_game2/pvz_demo.py` 直接运行

## 提交规范（公开仓库交付物）

- 仓库须公开（https://github.com/yykxyyds/coding-agent），保留完整提交历史，不压缩不改写，截止后不再推送。
- 提交信息沿用现有前缀：`feat` / `docs` / `demo` / `chore` / `test`。
- 严禁入库：API key、`DeepSeekAPI.txt`（在仓库目录之外，勿复制进来）、任何含姓名/院校的文件（双盲）。
- 提交前 `git status` 确认无敏感文件混入；`.idea/` 等 IDE 产物不入库。

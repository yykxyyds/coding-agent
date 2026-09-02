# 编程智能体（Coding Agent）

## 简介
一个用 Python 实现的编程智能体：通过与大语言模型交互，自主读写文件、执行命令、联网调研，完成编程与调研任务。核心是 agent loop——"想一步、做一步、看结果、再想"，循环直到任务完成。

## 运行方式
仅依赖 Python 标准库，无任何第三方依赖。API key 自动从项目上级目录的 DeepSeekAPI.txt 读取（或设 DEEPSEEK_API_KEY 环境变量），双击 .bat 即可启动。
1. 一键交互对话：双击 `run_interactive.bat`（交互命令：exit 退出、/clear 清空、/compact 压缩、/resume [ID] 恢复、/loop <间隔> 任务 定时执行）
2. 一键任务演示：双击 `run_task1_analysis.bat`（Excel 成绩数据分析，自动出中文报告）
3. 命令行（自定义工作目录）：`python agent.py --workdir <任务目录> --task "你的任务"``

## 特色
1. 零第三方依赖：仅用 Python 标准库（urllib 直连 DeepSeek、subprocess 执行命令）。
2. 五个关键逻辑全部自写：对话历史与上下文管理、工具定义与本地执行、模型输出解析、循环终止条件、错误处理。
3. 上下文压缩管理：历史超长自动压缩（更老对话交给模型总结成摘要、保留最近轮次原样），交互 /compact 手动压缩，长任务不爆上下文。
4. 工具定义：run_bash 执行命令、read_file / write_file 读写文件、web_search / web_fetch 联网搜索与抓取正文；本地执行、路径沙箱限制在工作目录内。
5. 会话持久化：历史对话自动存盘，/resume 恢复续跑，上下文跨任务累积。
6. 定时循环：/loop <间隔> 任务 定时自动激活 agent，按 ESC 停止。
7. 错误处理：命令超时、工具失败、路径越界、API/网络异常均有兜底，错误作为工具结果回传模型自行调整策略。

## 未来的改进方向
- 多模型接入：目前固定 DeepSeek，未来抽象为可配置模型层，支持切换多家模型。
- 更丰富的工具：在 bash/文件/联网基础上，扩展文件搜索、图片查看等，扩大任务覆盖面。
- 任务规划（/plan 模式）：复杂任务先拆解子任务、再逐步执行，提升可控性。
- 并行子 Agent（fan out）：把互不依赖的子任务分发给多个 agent 并行处理，加快复杂调研。
- Skill 机制：支持 agent 自行沉淀、编写可复用的 skill，逐步打磨成个人专属 coding agent。

## 演示
- task_test/task1_analysis：Excel 数据分析（240 行成绩 → 中文报告）
- task_test/task2_game：贪吃蛇（tkinter 版，零依赖）
- task_test/task3_game2：植物大战僵尸精简复刻（tkinter 版，零依赖）
- task_test/task4_research：联网调研主流 LLM API 价格 → 生成 PDF 分析报告

## 备注
- API key 仅经环境变量提供，不写入仓库。
- 仓库保留完整提交历史，便于评审了解开发过程。
- Git 仓库地址：https://github.com/yykxyyds/coding-agent

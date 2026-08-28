# 编程智能体（Coding Agent）

## 简介
一个用 Python 实现的编程智能体：通过与大语言模型交互，自主读写文件、执行命令，完成编程任务。核心是一个 agent loop——"想一步、做一步、看结果、再想"，循环直到任务完成。

## 运行方式
仅依赖 Python 标准库，无任何第三方依赖。
1. 设置 API key：`set DEEPSEEK_API_KEY=<你的 key>`（只从环境变量读取，不写入代码）
2. 进入项目目录，启动：
   - 交互式：`python agent.py --workdir <任务目录>`
   - 一次性任务：`python agent.py --workdir <任务目录> --task "你的任务"`
   - 无 key 体验：`python agent.py --mock`
3. 示例：`python agent.py --workdir . --task "demo_bugs/counter.py 运行结果不对，帮我修复"`——agent 会查看目录、读代码、运行定位、修改、再运行验证。

## 特色
- 零第三方依赖：仅用 Python 标准库（urllib 直连 DeepSeek、subprocess 执行命令）。
- 五个关键逻辑全部自写：对话历史与上下文管理、工具定义与本地执行、模型输出解析、循环终止条件、错误处理。
- 换任务只换一句 prompt：同一 agent 可修 bug、算 Excel 平均分、从零写工具、联网调研，代码不改。
- 能自主联网：自行搜索、抓取官方文档，生成带表格的 PDF 调研报告。
- 无 key 可自测：--mock 用预设脚本模拟模型跑通 loop，self_test.py 含 11 项自动化断言。

## 演示
- demo_bugs：修 bug（单词统计 counter.py，计数恒为 1）
- demo_excel：Excel 平均分
- demo_todo：从零写待办工具 + 测试
- demo_report：联网调研报告（搜索 + 抓文档 → 表格 → PDF）
- demo_analysis：Excel 数据分析（240 行成绩：读数据 → 算指标 → 分组对比 → 中文报告）

## 备注
- API key 仅经环境变量提供，不写入仓库。
- 仓库保留完整提交历史，便于评审了解开发过程。
- Git 仓库地址：https://github.com/yykxyyds/coding-agent

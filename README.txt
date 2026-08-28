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
3. 示例：`python agent.py --workdir . --task "分析 demo_analysis/class_scores.xlsx 学生成绩，生成中文报告"`——agent 会查看目录、读数据、写脚本运行、再验证结果。

## 特色
- 零第三方依赖：仅用 Python 标准库（urllib 直连 DeepSeek、subprocess 执行命令）。
- 五个关键逻辑全部自写：对话历史与上下文管理、工具定义与本地执行、模型输出解析、循环终止条件、错误处理。
- 换任务只换一句 prompt：同一 agent 换个任务描述即可，代码不改。
- 无 key 可自测：--mock 用预设脚本模拟模型跑通 loop 的完整流程。

## 演示
- demo_analysis：Excel 数据分析（240 行成绩：读数据 → 算指标 → 分组对比 → 中文报告）

## 备注
- API key 仅经环境变量提供，不写入仓库。
- 仓库保留完整提交历史，便于评审了解开发过程。
- Git 仓库地址：https://github.com/yykxyyds/coding-agent

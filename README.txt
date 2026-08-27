# 编程智能体（Coding Agent）

## 简介
一个用 Python 实现的编程智能体：通过与大语言模型交互，自主读写文件、执行命令，完成编程任务。
核心是一个 agent loop——"想一步、做一步、看结果、再想"，循环直到任务完成。

## 运行方式
仅依赖 Python 标准库，无任何第三方依赖。

1. 设置 API key：`set DEEPSEEK_API_KEY=<你的 key>`（只从环境变量读取，不写入代码）
2. 进入项目目录
3. 启动：
   - 交互式：`python agent.py --workdir <任务目录>`
   - 一次性任务：`python agent.py --workdir <任务目录> --task "你的任务"`
   - 无 key 体验：`python agent.py --mock`（用预设脚本模拟模型，跑通 loop）

示例（修复 demo 中的 bug）：
`python agent.py --workdir . --task "demo_bugs/counter.py 运行结果不对，帮我修复"`
agent 会自主完成：查看目录 → 读代码 → 运行定位问题 → 修改 → 再运行验证。

## 实现
- 模型：调用 DeepSeek（OpenAI 兼容 /chat/completions），使用其原生 tool calling。
- Agent loop：每轮把对话历史与工具定义发给模型；若模型请求调用工具，则在本地执行并把结果回填，继续循环；模型不再请求工具即视为完成，另有最大步数保护。
- 工具：run_bash（执行命令，带超时）、read_file、write_file（均限制在工作目录内）。
- 关键逻辑全部自行实现：对话历史与上下文管理（超长自动截断）、工具的定义与本地执行、模型输出的解析（tool_calls）、循环终止条件、错误处理（命令超时/文件异常/API 失败）。

## 演示
`demo_bugs/` 内含一个有 bug 的单词统计程序 counter.py（累加逻辑错误，各词计数恒为 1）。
运行上述命令即可让 agent 定位并修复，统计结果恢复正确（the 出现 3 次）。

## 备注
- API key 仅经环境变量提供，不写入仓库。
- Git 仓库地址：<待填写>

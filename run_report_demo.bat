@echo off
cd /d "%~dp0"
for /f "usebackq delims=" %%k in ("..\DeepSeekAPI.txt") do set "DEEPSEEK_API_KEY=%%k"
echo [1/2] 启动真实演示：联网调研报告...
echo [2/2] agent 将自主联网搜索、抓取官方文档、生成 PDF 调研报告
python -u agent.py --workdir . --max-steps 30 --task "请自主完成一次联网调研，产出一份 PDF 调研报告。调研主题：DeepSeek 官方 API 的模型、上下文长度与价格。你需要自己上网找资料，通过 run_bash 调用项目里的辅助命令：1. python web_fetch.py --search 关键词（搜索返回标题链接摘要）；2. python web_fetch.py URL（抓取网页正文）；3. python html_to_pdf.py 输入.html 输出.pdf（HTML 转 PDF）。建议：先抓取官方文档页 https://api-docs.deepseek.com/quick_start/pricing 提炼各模型的名称、上下文长度、输入输出价格，写成 demo_report/report.html（含数据表格和一段结论），再转成 demo_report/DeepSeek_API调研报告.pdf，最后列出 demo_report 目录确认 PDF 已生成。注意只修改 demo_report 目录内的文件。"
pause

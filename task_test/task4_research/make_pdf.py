# -*- coding: utf-8 -*-
"""生成《国内主流LLM厂商API价格调研分析报告》PDF"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------- 注册中文字体 ----------
pdfmetrics.registerFont(TTFont("MSYH", "C:/Windows/Fonts/msyh.ttc"))
pdfmetrics.registerFont(TTFont("MSYHBD", "C:/Windows/Fonts/msyhbd.ttc"))

FONT = "MSYH"
FONTB = "MSYHBD"

# ---------- 样式 ----------
def S(name, **kw):
    base = dict(fontName=FONT, fontSize=10.5, leading=17, alignment=TA_JUSTIFY, spaceAfter=6)
    base.update(kw)
    return ParagraphStyle(name, **base)

st_title = ParagraphStyle("title", fontName=FONTB, fontSize=20, leading=28,
                          alignment=TA_CENTER, spaceAfter=4)
st_sub   = ParagraphStyle("sub", fontName=FONT, fontSize=11, leading=16,
                          alignment=TA_CENTER, textColor=colors.HexColor("#666666"), spaceAfter=20)
st_h1    = ParagraphStyle("h1", fontName=FONTB, fontSize=15, leading=22,
                          spaceBefore=14, spaceAfter=8)
st_h2    = ParagraphStyle("h2", fontName=FONTB, fontSize=12.5, leading=18,
                          spaceBefore=10, spaceAfter=6)
st_body  = ParagraphStyle("body", fontName=FONT, fontSize=10.5, leading=17,
                          alignment=TA_JUSTIFY, spaceAfter=6)
st_note  = ParagraphStyle("note", fontName=FONT, fontSize=8.5, leading=13,
                          textColor=colors.HexColor("#888888"), alignment=TA_LEFT)
st_piccap= ParagraphStyle("piccap", fontName=FONT, fontSize=9, alignment=TA_CENTER,
                          textColor=colors.HexColor("#555555"), spaceBefore=2, spaceAfter=8)

OUT = "国内主流LLM厂商API价格调研分析报告.pdf"
doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                        topMargin=2*cm, bottomMargin=2*cm,
                        title="国内主流LLM厂商API价格调研分析报告",
                        author="AI研究员")
story = []

# ============ 封面 ============
story.append(Paragraph("国内主流 LLM 厂商 API 价格调研分析报告", st_title))
story.append(Paragraph("—— 市场格局 · 价格对比 · 成本测算 · 选型建议 ——", st_sub))

# ============ 摘要 ============
story.append(Paragraph("摘  要", st_h1))
story.append(Paragraph(
    "随着国内大模型进入商业化深水区，API 按量计价已成为企业级 AI 应用的基础成本单元。本报告针对国内主流大模型厂商"
    "（DeepSeek、阿里云通义千问、智谱 GLM、月之暗面 Kimi、字节跳动脉动豆包、百度文心、MiniMax 等）的 API 定价体系进行"
    "联网调研与横向对比，梳理各家的旗舰与经济档定价、计费规则、免费额度与优惠策略，并结合不同业务场景给出可落地的"
    "选型与成本优化建议。报告数据主要来源于各厂商 2026 年官方定价文档与开放平台，供技术决策与预算评估参考。", st_body))

# ============ 一、行业背景 ============
story.append(Paragraph("一、行业背景与市场格局", st_h1))
story.append(Paragraph("1.1 大模型 API 商业化进入“百模大战 + 价格战”阶段", st_h2))
story.append(Paragraph(
    "2024 年以来，国内大模型 API 价格经历了多轮显著下调，“百万 Token 从千元级下探到个位数甚至角分级”。尤其是 2025—2026 年，"
    "随着 MoE（混合专家）架构、稀疏注意力、线性注意力、推理引擎优化与国产算力的成熟，长上下文推理的单位成本大幅下降，"
    "旗舰模型与经济型模型之间形成了清晰的“价格分层”。企业在选型时，已从单纯“选最强模型”转向“按任务匹配模型 + 控本”。", st_body))
story.append(Paragraph("1.2 主要玩家与定位", st_h2))
story.append(Paragraph(
    "当前国内具备规模化 API 服务能力的主流厂商可大致分为三类："
    "（1）云厂商：通义千问（阿里云百炼），依托阿里云全栈能力，模型体系最全、生态最完善；"
    "（2）独立模型公司：DeepSeek（深度求索，以极致性价比与开源著称）、智谱 GLM（清华系，旗舰+Free 免费模型矩阵）、"
    "月之暗面 Kimi（长上下文与编程 Agent 见长）、MiniMax（多模态+长上下文）等；"
    "（3）互联网巨头：字节跳动豆包（火山方舟/火山引擎，主打低价与大规模应用）、百度文心（ERNIE，老牌中文搜索引擎背景）。", st_body))

# ============ 二、价格详表 ============
story.append(Paragraph("二、主流厂商 API 定价详表", st_h1))

price_rows = [
    ("厂商", "代表性模型", "上下文", "输入(元/M)", "输出(元/M)", "备注"),
    ("DeepSeek", "V4-Flash", "1M", "3.0(高峰)", "9.0(高峰)", "空闲时段半价；缓存命中低至0.1元"),
    ("DeepSeek", "V4-Pro", "1M", "9.0(高峰)", "27.0(高峰)", "旗舰；空闲半价"),
    ("阿里云", "Qwen3-max", "高", "2.5(≤32K)", "10.0", "阶梯计费；新用户100万免费Token"),
    ("阿里云", "Qwen7-plus", "256K/1M", "2.0", "8.0", "Batch半价"),
    ("阿里云", "Qwen-plus", "128K+", "0.8", "2.0", "经济型；Batch半价"),
    ("阿里云", "Qwen-max(旧)", "—", "2.4", "9.6", "经典版"),
    ("智谱", "GLM-5.3", "1M", "约6.0", "约20.0", "旗舰，编程/Agent强"),
    ("智谱", "GLM-5.3-Flash", "1M", "约0.6", "约2.0", "原生多模态；约GLM-5.3的1/10"),
    ("智谱", "GLM-4.x-Flash", "128K-200K", "免费", "免费", "多款免费文本/视觉模型"),
    ("月之暗面 Kimi", "Kimi K3", "1M", "约5.0", "约16.0", "2.8万亿参数旗舰，长程编程"),
    ("字节豆包", "Doubao-Pro", "128K+", "约0.8", "约2.0", "火山方舟，主打低价"),
    ("百度", "ERNIE-4.0", "128K", "约0.5", "约2.0", "文心旗舰"),
    ("MiniMax", "MiniMax-M1", "长", "约1.0", "约8.0", "多模态旗舰"),
]
price_tbl = Table(price_rows, colWidths=[2.7*cm, 3.3*cm, 1.9*cm, 3.2*cm, 2.9*cm, 4.6*cm])
price_tbl.setStyle(TableStyle([
    ("FONTNAME", (0,0), (-1,0), FONTB),
    ("FONTNAME", (0,1), (-1,-1), FONT),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563A6")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#EEF3FA")]),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#B8C6D9")),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ("LEFTPADDING", (0,0), (-1,-1), 4),
    ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
story.append(price_tbl)
story.append(Paragraph(
    "注：价格单位为人民币元/百万 Token，表格取自各厂商 2026 年官方定价（含高峰/标准档）。DeepSeek、阿里云通义千问为官网确认价格，"
    "其余厂商价格为主要档位市场公开口径，带“约”字为测算值，具体以各平台实时页面为准。输出价格通常显著贵于输入（约 3~4 倍）。", st_note))

story.append(Paragraph("2.1 DeepSeek（深度求索）—— 极致性价比的“价格屠夫”", st_h2))
story.append(Paragraph(
    "DeepSeek 凭借自研 MoE 训练框架、万卡智算集群与高效推理引擎，长期以低于行业数量级的价格提供接近一线能力的前沿模型。"
    "据官方定价文档，其 V4-Flash 高峰时段输入（缓存未命中）约 3 元/百万 Token、输出约 9 元；V4-Pro 输入约 9 元、输出约 27 元；"
    "非高峰时段（工作日 9:00–12:00、14:00–18:00 之外）一律半价；缓存命中输入可低至 0.05–0.1 元/百万 Token。"
    "1M 上下文、支持思考/非思考双模式，并兼容 OpenAI 与 Anthropic API 格式，迁移成本极低。", st_body))

story.append(Paragraph("2.2 阿里云通义千问 —— 模型矩阵最全的一站式选择", st_h2))
story.append(Paragraph(
    "阿里云百炼提供从旗舰 Qwen3.8-Max（输入约 12 元/百万、输出约 36 元）到经济型 Qwen-plus（输入 0.8 元、输出 2 元）的完整阶梯，"
    "并设置基于单次请求输入 Token 总量的“阶梯计费”（Token 越多单价越高），同时支持 Batch 调用半价与上下文缓存折扣。"
    "绝大多数千问模型为新用户提供 100 万 Token 免费额度（有效期 90 天），并依托阿里云生态，从文本、图像、视频、语音到向量检索全覆盖，"
    "是云原生企业的稳妥之选。", st_body))

story.append(Paragraph("2.3 智谱 GLM —— 清华系，免费模型矩阵最丰富", st_h2))
story.append(Paragraph(
    "智谱面向个人开发者打出“普惠牌”，不仅提供 GLM-5.3 旗舰（1M 上下文、编程/Agent 能力比肩 Claude），更推出了定价仅为旗舰约 1/10 的"
    "GLM-5.3-Flash 原生多模态模型，以及多款完全免费的文本与视觉模型（GLM-4.7-Flash、GLM-4.5-Flash、GLM-4-Flash、GLM-4V-Flash 等），"
    "极为适合做原型验证、教学与低成本量产。其 GLM Coding Plan 订阅套餐还提供“积分制”额度，非高峰时段积分减半，性价比突出。", st_body))

story.append(Paragraph("2.4 月之暗面 Kimi —— 长上下文与编程 Agent 旗舰", st_h2))
story.append(Paragraph(
    "Kimi K3 为 2.8 万亿参数、1M Token 上下文旗舰，面向长程编程与端到端知识工作；Kimi K2.7 Code 为编程专用模型，支持 256K 上下文与多模态输入"
    "并提供高速档（highspeed）。Kimi 在“长文档 + Agent 场景”表现突出，常被用于 Claude Code、Codex 等编程工具链，"
    "定价位于中高端，但长上下文场景下的“性价比”突出。", st_body))

story.append(Paragraph("2.5 字节豆包 / 百度文心 / MiniMax", st_h2))
story.append(Paragraph(
    "火山引擎豆包（Doubao）以“低价 + 大规模应用”著称，Pro 级模型定价与通义经济型相当，适合高并发、对成本敏感的 To C 场景；"
    "百度文心 ERNIE 依托中文语料积累，旗舰 ERNIE-4.0 定价不高，适合中文搜索语义与知识类任务；MiniMax 在多模态（图像/视频/音频对话）"
    "与长上下文推理上特色鲜明，其 M1 系列在中文长文本任务上具备竞争力。", st_body))

# ============ 三、图表 ============
story.append(Paragraph("三、价格横向对比图", st_h1))
story.append(Image("report_assets/price_input.png", width=16*cm, height=16*cm*5.2/9))
story.append(Paragraph("图 1  各厂商代表性模型 API 输入价格对比（元/百万 Token）", st_piccap))
story.append(Image("report_assets/price_output.png", width=16*cm, height=16*cm*5.2/9))
story.append(Paragraph("图 2  各厂商代表性模型 API 输出价格对比（元/百万 Token）", st_piccap))
story.append(Image("report_assets/cost_total.png", width=16*cm, height=16*cm*5.2/9))
story.append(Paragraph("图 3  单次典型调用（输入 1M + 输出 2M Token）的估算总成本对比（元）", st_piccap))

# ============ 四、计费要点与成本优化 ============
story.append(Paragraph("四、计费规则要点与成本优化策略", st_h1))
story.append(Paragraph("4.1 影响 API 实际成本的关键变量", st_h2))
for t in [
    "① 输入 vs 输出单价严重不对称：绝大多数厂商输出单价为输入的 3~4 倍，因此应尽量让模型输出精炼、避免废话生成。",
    "② 缓存大幅降本：系统提示词与长文档多次命中缓存时，输入价格可降低 90% 以上（如 DeepSeek 缓存命中仅约 0.05–0.1 元）。构造请求应充分复用稳定上下文。",
    "③ 高峰/非高峰差异化定价：部分厂商（DeepSeek、智谱）对非高峰时段的调用给予半价优惠，可错峰运行批量任务。",
    "④ 阶梯计费：阿里云等按单次输入 Token 总量分档，长 prompt 会导致整单上浮，需权衡上下文长度。",
    "⑤ Batch 调用：支持异步批量调用的模型通常按实时价格半价计费（如千问系列）。",
    "⑥ 免费额度 / 订阅套餐：新用户免费额度（如阿里 100 万 Token）、智谱免费 Flash 模型、GLM Coding Plan 积分制等，可显著拉低前期成本。",
]:
    story.append(Paragraph(t, st_body))
story.append(Paragraph("4.2 成本优化清单", st_h2))
story.append(Paragraph(
    "（1）优先使用缓存与稳定系统提示词；（2）对非实时、可容忍延迟的任务采用 Batch/异步调用；（3）高峰任务错峰到非高峰时段执行；"
    "（4）按任务复杂度分流——简单任务路由到经济版/免费模型，复杂推理才上旗舰；（5）用免费额度与体验券完成原型与 POC；"
    "（6）对长上下文需求，优先选择缓存/低价输入模型（DeepSeek、Kimi 等）；（7）监控每 1 元钱产出的 Token 数与业务转化，建立成本看板。", st_body))

# ============ 五、选型建议 ============
story.append(Paragraph("五、分场景选型建议", st_h1))
adv_rows = [
    ("应用场景", "推荐厂商/模型", "核心理由"),
    ("通用对话/客服/内容生成", "通义 Qwen-plus、豆包 Doubao-Pro、智谱 GLM-5.3-Flash", "经济型定价低，稳定成熟，量大控本"),
    ("复杂推理/数据分析/智能体", "DeepSeek V4-Pro、Kimi K3、GLM-5.3", "旗舰推理强，Agent 长程任务表现佳"),
    ("编程与代码生成（IDE）", "Kimi K2.7 Code、GLM-5.3/5.3-Flash、DeepSeek", "深度适配 Claude Code/Codex 等工具"),
    ("长文档/百万级上下文", "DeepSeek、Kimi K3、GLM-5.3（1M 上下文）", "长上下文 + 缓存降本"),
    ("中文语义/搜索/知识问答", "百度文心 ERNIE、通义千问", "中文语料与搜索生态优势"),
    ("教学/原型/低成本量产", "智谱 GLM Flash 系列（免费）、DeepSeek", "免费或极低，上手门槛低"),
    ("多模态（图/视频/语音）", "通义千问、MiniMax、豆包", "全模态覆盖，场景化解决方案"),
    ("高并发 To C 大规模应用", "字节豆包、通义 Qwen-plus", "低价 + 高吞吐 + 生态基建"),
]
adv_tbl = Table(adv_rows, colWidths=[4.2*cm, 6.6*cm, 6.0*cm])
adv_tbl.setStyle(TableStyle([
    ("FONTNAME", (0,0), (-1,0), FONTB),
    ("FONTNAME", (0,1), (-1,-1), FONT),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563A6")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#EEF3FA")]),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#B8C6D9")),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (-1,-1), 4),
    ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
story.append(adv_tbl)

# ============ 六、综合建议 ============
story.append(Paragraph("六、综合建议", st_h1))
story.append(Paragraph(
    "1. 多模型策略是主流。单一厂商很难在所有维度（成本、推理、长上下文、多模态）同时最优，建议采用“路由网关”按任务复杂度"
    "与经济性自动分流，实现效果与成本的平衡。"
    "2. 成本敏感业务优先看“输出单价 × 输出量”。输出最贵，先把 prompt 与输出长度约束做扎实，再谈选型。"
    "3. 重推理 / 长文档场景，DeepSeek 与 Kimi 的“缓存 + 非高峰半价”是最省钱的路径。"
    "4. 熟悉云的团队优先选阿里云百炼，模型矩阵最全、Batch/缓存/阶梯规则透明，且与云资源天然打通。"
    "5. 原型与轻量产品从免费/低价模型起步（智谱 Flash、通义 Qwen-plus、DeepSeek），指标达标后再升级。"
    "6. 持续跟踪价格变动。国内大模型价格仍在快速下行，建议每季度复核一次，及时切换更优档位。", st_body))

# ============ 声明 ============
story.append(Spacer(1, 10))
story.append(Paragraph(
    "声明：本报告数据来源于各厂商 2026 年公开官方定价与开放文档（含 DeepSeek API 文档、阿里云百炼计费文档、智谱 BigModel 文档、"
    "Moonshot Kimi 开放平台、火山引擎火山方舟等）。部分厂商价格页为动态渲染，报告中的少数价格采用市场公开口径测算，最终以各平台实时"
    "控制台与对账单为准。本报告仅供选型与预算评估参考，不构成任何投资或商务承诺。", st_note))

doc.build(story)
print("PDF 已生成:", os.path.abspath(OUT))

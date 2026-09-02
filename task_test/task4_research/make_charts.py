# -*- coding: utf-8 -*-
"""生成价格对比图表 -> report_assets/*.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

# 注册中文字体
for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
    try:
        font_manager.fontManager.addfont(fp)
    except Exception as e:
        print("font-skip", fp, e)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

import os
os.makedirs("report_assets", exist_ok=True)

# ============ 数据（输入/输出 价格，元/百万token，标准档位）============
# 模型: (输入价格, 输出价格, 厂商)
models = [
    # DeepSeek（分别取高峰价/标准价）
    ("DeepSeek V4-Flash", 3.0, 9.0, "DeepSeek"),
    ("DeepSeek V4-Pro", 9.0, 27.0, "DeepSeek"),
    # 阿里云千问
    ("通义 Qwen-max(旧)", 2.4, 9.6, "阿里云"),
    ("通义 Qwen3-max", 2.5, 10.0, "阿里云"),
    ("通义 Qwen7-plus", 2.0, 8.0, "阿里云"),
    ("通义 Qwen-plus", 0.8, 2.0, "阿里云"),
    # 智谱
    ("智谱 GLM-5.3", 6.0, 20.0, "智谱"),
    ("智谱 GLM-5.3-Flash", 0.6, 2.0, "智谱"),
    # Kimi
    ("Kimi K3", 5.0, 16.0, "Kimi(Moonshot)"),
    # 豆包（火山引擎）
    ("豆包 Doubao-Pro", 0.8, 2.0, "字节豆包"),
    # 百度文心
    ("文心 ERNIE-4.0", 0.5, 2.0, "百度"),
    # MiniMax
    ("MiniMax-M1", 1.0, 8.0, "MiniMax"),
]

# 按输入价格升序
models.sort(key=lambda x: x[1])

names = [m[0] for m in models]
inputs = [m[1] for m in models]
outputs = [m[2] for m in models]
colors = {
    "DeepSeek": "#4C78A8",
    "阿里云": "#F58518",
    "智谱": "#E45756",
    "Kimi(Moonshot)": "#72B7B2",
    "字节豆包": "#54A24B",
    "百度": "#B279A2",
    "MiniMax": "#F2CF5B",
}
c = [colors[m[3]] for m in models]

# ============ 图1：输入价格对比（对数or线性）============
fig, ax = plt.subplots(figsize=(9, 5.2))
y = np.arange(len(names))[::-1]
bars = ax.barh(y, inputs, color=c, height=0.6)
for yi, v in zip(y, inputs):
    ax.text(v + 0.05, yi, f"{v:.1f} 元", va="center", fontsize=8.5)
ax.set_yticks(y)
ax.set_yticklabels(names, fontsize=9)
ax.set_xlabel("输入价格（元 / 百万 Token）[同档：≤32K/标准]", fontsize=10)
ax.set_title("国内主流大模型 API 输入价格对比", fontsize=13, fontweight="bold")
ax.set_xlim(0, max(inputs) * 1.35)
ax.grid(axis="x", linestyle="--", alpha=0.4)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
plt.tight_layout()
plt.savefig("report_assets/price_input.png", dpi=150)
plt.close()

# ============ 图2：输出价格对比 ============
fig, ax = plt.subplots(figsize=(9, 5.2))
y = np.arange(len(names))[::-1]
bars = ax.barh(y, outputs, color=c, height=0.6)
for yi, v in zip(y, outputs):
    ax.text(v + 0.5, yi, f"{v:.1f} 元", va="center", fontsize=8.5)
ax.set_yticks(y)
ax.set_yticklabels(names, fontsize=9)
ax.set_xlabel("输出价格（元 / 百万 Token）", fontsize=10)
ax.set_title("国内主流大模型 API 输出价格对比", fontsize=13, fontweight="bold")
ax.set_xlim(0, max(outputs) * 1.4)
ax.grid(axis="x", linestyle="--", alpha=0.4)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
plt.tight_layout()
plt.savefig("report_assets/price_output.png", dpi=150)
plt.close()

# ============ 图3：各厂商旗舰 vs 经济档 输入输出总成本（组合条形） ============
fig, ax = plt.subplots(figsize=(9, 5.2))
# 选取代表性模型，展示"输入+输出"合计(假设 输入:输出 = 1:2 tokens)
sel = [
    ("通义 Qwen-plus", 0.8, 2.0),
    ("DeepSeek V4-Flash", 3.0, 9.0),
    ("豆包 Doubao-Pro", 0.8, 2.0),
    ("智谱 GLM-5.3-Flash", 0.6, 2.0),
    ("通义 Qwen3-max", 2.5, 10.0),
    ("Kimi K3", 5.0, 16.0),
    ("智谱 GLM-5.3", 6.0, 20.0),
    ("DeepSeek V4-Pro", 9.0, 27.0),
]
sel.sort(key=lambda x: x[1] + 2 * x[2])
sn = [s[0] for s in sel]
sc = ["#54A24B" if s[1]+2*s[2] < 10 else ("#F58518" if s[1]+2*s[2] < 30 else "#E45756") for s in sel]
# 假设一次调用：输入1MI tokens + 输出2M tokens 总成本
total = [s[1] + 2 * s[2] for s in sel]
y = np.arange(len(sn))[::-1]
ax.barh(y, total, color=sc, height=0.55)
for yi, v in zip(y, total):
    ax.text(v + 0.5, yi, f"{v:.1f} 元", va="center", fontsize=9)
ax.set_yticks(y)
ax.set_yticklabels(sn, fontsize=9)
ax.set_xlabel("估算总成本（输入 1M + 输出 2M Token，元）", fontsize=10)
ax.set_title("单次典型调用估算总成本对比（输入 1M + 输出 2M Token）", fontsize=12, fontweight="bold")
ax.set_xlim(0, max(total) * 1.35)
ax.grid(axis="x", linestyle="--", alpha=0.4)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
plt.tight_layout()
plt.savefig("report_assets/cost_total.png", dpi=150)
plt.close()

print("图表生成完成:", os.listdir("report_assets"))

# -*- coding: utf-8 -*-
"""
学生成绩数据分析脚本
分析 demo_analysis/class_scores.xlsx 并生成中文报告
"""
import pandas as pd

# 设置显示不被截断
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 200)

SRC = "demo_analysis/class_scores.xlsx"
OUT = "demo_analysis/analysis_report.txt"

df = pd.read_excel(SRC)
subjects = ["语文", "数学", "英语"]

# 计算总分
df["总分"] = df[subjects].sum(axis=1)

lines = []
def w(s=""):
    lines.append(s)

w("=" * 60)
w("《学生成绩分析报告》")
w("数据源：demo_analysis/class_scores.xlsx")
w("=" * 60)

# ---------- 1. 数据概览 ----------
w()
w("一、数据概览")
w("-" * 40)
w(f"数据行数（学生人数）：{len(df)}")
w(f"数据列数：{df.shape[1]}")
w(f"包含字段：{', '.join(df.columns.tolist())}")
w(f"班级数：{df['班级'].nunique()}（{'、'.join(sorted(df['班级'].unique()))}）")
gender_counts = df['性别'].value_counts().to_dict()
w(f"性别分布：男生 {gender_counts.get('男',0)} 人，女生 {gender_counts.get('女',0)} 人")
w(f"空值数量：{int(df.isnull().sum().sum())}")
w("数值列基本统计：")
w(df[subjects].describe().round(2).to_string())

# ---------- 2. 各科统计指标 ----------
w()
w("二、各科统计指标（平均分 / 最高分 / 最低分 / 及格率 / 优秀率）")
w("-" * 40)
w("说明：及格按 ≥60 计，优秀按 ≥90 计。")


def line_stats(s):
    avg = s.mean()
    mx = s.max()
    mn = s.min()
    pass_rate = (s >= 60).mean() * 100
    good_rate = (s >= 90).mean() * 100
    return avg, mx, mn, pass_rate, good_rate


w(f"{'科目':<6}{'平均分':>8}{'最高分':>8}{'最低分':>8}{'及格率':>10}{'优秀率':>10}")
for sub in subjects:
    avg, mx, mn, pr, gr = line_stats(df[sub])
    w(f"{sub:<6}{avg:>8.2f}{mx:>8.1f}{mn:>8.1f}{pr:>9.2f}%{gr:>9.2f}%")

# ---------- 3. 排行榜 ----------
w()
w("三、排行榜")
w("-" * 40)
w("（一）总分前 10 名：")
w(f"{'排名':<6}{'学号':<8}{'姓名':<6}{'班级':<6}{'性别':<6}{'语文':>6}{'数学':>6}{'英语':>6}{'总分':>8}")
top10 = df.nlargest(10, "总分")
for i, (_, r) in enumerate(top10.iterrows(), 1):
    w(f"{i:<6}{r['学号']:<8}{r['姓名']:<6}{r['班级']:<6}{r['性别']:<6}"
      f"{r['语文']:>6.1f}{r['数学']:>6.1f}{r['英语']:>6.1f}{r['总分']:>8.2f}")

w()
for sub in subjects:
    w(f"（二）{sub}单科前 5 名：")
    w(f"{'排名':<6}{'学号':<8}{'姓名':<6}{'班级':<6}{'性别':<6}{sub:>6}")
    top5 = df.nlargest(5, sub)
    for i, (_, r) in enumerate(top5.iterrows(), 1):
        w(f"{i:<6}{r['学号']:<8}{r['姓名']:<6}{r['班级']:<6}{r['性别']:<6}{r[sub]:>6.1f}")
    w()

# ---------- 4. 分组统计 ----------
w("四、分组统计与观察结论")
w("-" * 40)
w("（一）按班级统计各科平均分：")
class_g = df.groupby("班级")[subjects].mean().round(2)
w(class_g.to_string())
w()
w("班级平均总分（用于观察整体水平）：")
class_total_g = df.groupby("班级")["总分"].mean().round(2)
w(class_total_g.to_string())

w()
w("（二）按性别统计各科平均分：")
gender_g = df.groupby("性别")[subjects].mean().round(2)
w(gender_g.to_string())
w()
gender_total_g = df.groupby("性别")["总分"].mean().round(2)
w(gender_total_g.to_string())

w()
w("（三）按班级+性别统计各科平均分：")
cross_g = df.groupby(["班级", "性别"])[subjects].mean().round(2)
w(cross_g.to_string())

# ---------- 5. 观察结论 ----------
w()
w("五、观察与结论")
w("-" * 40)

# 找班级最优
best_class = class_total_g.idxmax()
worst_class = class_total_g.idxmin()
w(f"1. 整体水平：总分平均分最高的班级是【{best_class}】"
  f"（{class_total_g.max():.2f}），最低的是【{worst_class}】"
  f"（{class_total_g.min():.2f}），班级间存在一定差距。")

# 各科谁最均衡/最强
for sub in subjects:
    best_sub_cls = df.groupby("班级")[sub].mean().idxmax()
    best_sub_val = df.groupby("班级")[sub].mean().max()
    w(f"   - {sub}平均分最高的班级为 {best_sub_cls}（{best_sub_val:.2f}）。")

# 性别对比
gender_avg = gender_g
for sub in subjects:
    g = gender_avg.loc[:, sub]
    stronger = g.idxmax()
    diff = abs(g.loc['男'] - g.loc['女'])
    w(f"2. 性别差异：{sub}科目中【{stronger}】平均分更高，"
      f"男女生相差 {diff:.2f} 分。")

# 及格率/优秀率
avg_pass = sum((df[s] >= 60).mean() for s in subjects) / len(subjects) * 100
avg_good = sum((df[s] >= 90).mean() for s in subjects) / len(subjects) * 100
w(f"3. 总体看，各科平均及格率约 {avg_pass:.1f}%，优秀率约 {avg_good:.1f}%。")

# 各科强弱
strongest_sub = df[subjects].mean().idxmax()
weakest_sub = df[subjects].mean().idxmin()
w(f"4. 学科难度：学生整体平均分最高的是【{strongest_sub}】"
  f"（{df[strongest_sub].mean():.2f}），相对较弱的是【{weakest_sub}】"
  f"（{df[weakest_sub].mean():.2f}），建议在{weakest_sub}学科加强教学。")

# 总分最值
w(f"5. 总分最高 {df['总分'].max():.2f}，最低 {df['总分'].min():.2f}，"
  f"全距较大，学生成绩分布存在明显分化。")

# 写入文件
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("报告已生成：", OUT)
print("部分预览：")
print("\n".join(lines[:60]))

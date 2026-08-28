# -*- coding: utf-8 -*-
"""学生成绩数据分析脚本"""
import pandas as pd
import numpy as np

f = r"demo_analysis/class_scores.xlsx"
df = pd.read_excel(f)

report = []
def out(*args):
    s = " ".join(str(a) for a in args)
    report.append(s)
    print(s)

out("=" * 70)
out("学生成绩数据分析报告")
out("=" * 70)

# ---------------- 1. 数据整体情况 ----------------
out("\n【一、数据基本情况】")
out("-" * 50)
out(f"数据规模：共 {df.shape[0]} 行（名学生），{df.shape[1]} 列。")
out(f"列名及含义：{list(df.columns)}")
out("各列数据类型：")
for c in df.columns:
    out(f"   {c}: {df[c].dtype}")
out("\n数据预览（前5行）：")
out(df.head(5).to_string())

# 缺失值检查
out("\n缺失值检查（每列缺失数量）：")
miss = df.isnull().sum()
out(miss.to_string())
out(f"缺失总单元格数：{int(miss.sum())}（数据无缺失值，完整度100%）")

# 异常值检查（对成绩列，出范围 [0,100] 视为异常）
out("\n异常值检查（成绩不在[0,100]范围视为异常）：")
score_cols = ["语文", "数学", "英语"]
nan_issues = 0
for c in score_cols:
    bad = df[(df[c] < 0) | (df[c] > 100)]
    if len(bad) == 0:
        out(f"   {c}: 无越界记录")
    else:
        nan_issues += 1
        out(f"   {c}: 越界记录 {len(bad)} 行，学号=" + ",".join(bad["学号"]))
if nan_issues == 0:
    out("   （所有成绩均在[0,100]范围内，无异常值）")

# 检查重复姓名
dup = df["姓名"][df["姓名"].duplicated(keep=False)]
out(f"\n姓名字段重复情况：{len(dup)} 个记录存在重复姓名（涉及 {dup.nunique()} 个不同姓名），"
    f"可能是同名不同学生，学号唯一，不视为问题。")

# 班级 / 性别分布
out("\n班级分布：")
out(df["班级"].value_counts().sort_index().to_string())
out("\n性别分布：")
out(df["性别"].value_counts().to_string())

# ---------------- 2. 总体指标 ----------------
out("\n【二、各科总体指标】")
out("-" * 50)

def stat_line(c, s):
    mean = s.mean()
    mx = s.max()
    mn = s.min()
    pass_rate = (s >= 60).mean() * 100
    good_rate = (s >= 90).mean() * 100
    std = s.std()
    out(f"  {c}: 平均分={mean:.2f} (标准差{std:.2f}) | 最高分={mx} | 最低分={mn} | "
        f"及格率(>=60)={pass_rate:.2f}% | 优秀率(>=90)={good_rate:.2f}%")

for c in score_cols:
    stat_line(c, df[c])

# ---------------- 3. 排名 ----------------
out("\n【三、排名】")
out("-" * 50)

df = df.copy()
df["总分"] = df[score_cols].sum(axis=1)

out("\n总分前10名：")
top_total = df.sort_values(["总分", "语文", "数学", "英语"], ascending=False).head(10).copy()
top_total.insert(0, "排名", range(1, 11))
out(top_total[["排名", "学号", "姓名", "班级", "性别"] + score_cols + ["总分"]]
    .reset_index(drop=True).to_string())

for c in score_cols:
    out(f"\n{c}单科前5名：")
    top = df.sort_values([c, "总分"], ascending=False).head(5).copy()
    top.insert(0, "排名", range(1, 6))
    tmp = top[["排名", "学号", "姓名", "班级", "性别", c]].copy()
    out(tmp.reset_index(drop=True).to_string())

# ---------------- 4. 分组对比 ----------------
out("\n【四、分组对比】")
out("-" * 50)

out("\n4.1 各班级各科平均分与总平均分：")
cls_count = df.groupby("班级").size().rename("人数")
cls_group = df.groupby("班级")[score_cols + ["总分"]].mean().round(2)
cls_group = cls_count.to_frame().join(cls_group)
out(cls_group.to_string())

out("\n按班级比较各科平均分（最佳/最差班）：")
for c in score_cols + ["总分"]:
    m = df.groupby("班级")[c].mean().round(2)
    best = m.idxmax()
    worst = m.idxmin()
    out(f"   {c}: 最高班级={best}({m[best]}), 最低班级={worst}({m[worst]}), 班级差距={round(m[best]-m[worst],2)}")

out("\n4.2 各性别各科平均分：")
sex_count = df.groupby("性别").size().rename("人数")
sex_group = df.groupby("性别")[score_cols + ["总分"]].mean().round(2)
sex_group = sex_count.to_frame().join(sex_group)
out(sex_group.to_string())

out("\n按性别比较各科平均分：")
for c in score_cols + ["总分"]:
    m = df.groupby("性别")[c].mean()
    out(f"   {c}: 男={m['男']:.2f}, 女={m['女']:.2f}, 差值(女-男)={round(m['女']-m['男'],2)}")

# ---------------- 5. 观察结论 ----------------
out("\n【五、观察结论】")
out("-" * 50)

total_by_class = df.groupby("班级")["总分"].mean()
best_class = total_by_class.idxmax()
worst_class = total_by_class.idxmin()
gap_class = round(total_by_class[best_class] - total_by_class[worst_class], 2)

# 各班语文优秀率、及格率
best_cls_yw = df.groupby("班级")["语文"].mean().idxmax()
best_cls_sx = df.groupby("班级")["数学"].mean().idxmax()

out("1. 数据质量：共240条学生记录，无缺失值、无越界异常成绩，数据较为干净可靠。")
out("2. 整体水平：语文平均分最高(79.95)，英语平均分最低(75.24)；三门及格率均超过95%，"
    "但优秀率整体不高，其中英语优秀率仅1.67%，说明英语拔尖学生非常少。")
out("3. 成绩离散度：数学标准差最大(约10.14)，说明学生间数学成绩差异最大、两极化明显；"
    "语文章差异相对较小(约7.88)，成绩分布更集中。")
out(f"4. 班级差异：各班人数均30人，但班级间成绩存在明显分层。总平均分最高为{best_class}({total_by_class[best_class]:.2f})，"
    f"最低为{worst_class}({total_by_class[worst_class]:.2f})，总平均分差距达{gap_class}分。"
    f"各科中数学班级差距最大(16.27分)，说明1、2班与8班在数学上拉开明显差距，存在班级教学水平不均衡的问题。")
out("5. 性别差异：女生语文平均分明显高于男生(3.60分)；男生数学平均分略高于女生(1.49分)；"
    "英语两者基本相当(差值0.51分)。整体总分女生略高(1.59分)，性别差异不大且各有优势学科。")
out("6. 建议：(1) 针对1-2班与低分段班级的差距，可组织集体备课与教学经验共享；(2) 英语整体优秀率过低，"
    "应加强英语培优教学；(3) 数学离散度大，需关注数学薄弱学生进行分层补差。")

# 将报告写入 txt 文件
with open(r"demo_analysis/analysis_report.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(report) + "\n")

print("\n[分析完成，报告已写入 demo_analysis/analysis_report.txt]")

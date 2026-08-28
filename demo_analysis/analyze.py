# -*- coding: utf-8 -*-
import pandas as pd

SRC = 'demo_analysis/class_scores.xlsx'
OUT = 'demo_analysis/analysis_report.txt'

subjects = ['语文', '数学', '英语']

df = pd.read_excel(SRC)

lines = []
def w(s=''):
    lines.append(str(s))

# ---------- 1. 数据概览 ----------
w('=' * 60)
w('一、数据概览')
w('=' * 60)
w(f'数据总条数（学生人数）：{len(df)}')
w(f'字段：{"、".join(df.columns.tolist())}')
w(f'班级分布：{"、".join(df["班级"].unique())}')
w(f'性别：{"、".join(df["性别"].unique())}')
w('缺失值统计：')
for col in df.columns:
    w(f'  {col}：缺失 {df[col].isnull().sum()} 条')
w('')
w('各科目数据概况（最小值 / 最大值 / 均值）：')
for s in subjects:
    w(f'  {s}：最低 {df[s].min()}，最高 {df[s].max()}，平均 {df[s].mean():.2f}')
w('')
w('班级人数：')
class_counts = df.groupby('班级').size()
for c, n in class_counts.items():
    w(f'  {c}：{n} 人')
w('')
w('性别人数：')
for g, n in df.groupby('性别').size().items():
    w(f'  {g}：{n} 人')
w('')

# ---------- 2. 单科统计 ----------
w('=' * 60)
w('二、各科平均分 / 最高分 / 最低分 / 及格率 / 优秀率')
w('=' * 60)
pass_rate = lambda x: (x >= 60).mean() * 100
excell_rate = lambda x: (x >= 90).mean() * 100

for s in subjects:
    avg = df[s].mean()
    hi = df[s].max()
    lo = df[s].min()
    pr = pass_rate(df[s])
    er = excell_rate(df[s])
    w(f'【{s}】')
    w(f'  平均分：{avg:.2f}')
    w(f'  最高分：{hi}')
    w(f'  最低分：{lo}')
    w(f'  及格率（≥60）：{pr:.1f}%')
    w(f'  优秀率（≥90）：{er:.1f}%')
    w('')

# ---------- 3. 总分排序 ----------
w('=' * 60)
w('三、总分排名')
w('=' * 60)
df['总分'] = df[subjects].sum(axis=1)
df['平均分'] = df[subjects].mean(axis=1)

total_top10 = df.nlargest(10, '总分')
w('总分排名前10：')
for i, (_, row) in enumerate(total_top10.iterrows(), 1):
    w(f'  第{i}名：{row["学号"]} {row["姓名"]}（{row["班级"]}，{row["性别"]}）总分 {row["总分"]:.1f} 平均 {row["平均分"]:.1f}')
w('')

w('各单科前5：')
for s in subjects:
    top5 = df.nlargest(5, s)
    w(f'【{s}】前5：')
    for i, (_, row) in enumerate(top5.iterrows(), 1):
        w(f'  第{i}名：{row["学号"]} {row["姓名"]}（{row["班级"]}，{row["性别"]}）{s} {row[s]}')
    w('')

# ---------- 4. 分组统计 ----------
w('=' * 60)
w('四、按班级、性别分组统计各科平均分')
w('=' * 60)

w('按班级分组各科平均分：')
by_class = df.groupby('班级')[subjects].mean().round(2)
w(by_class)
w('')
w('按性别分组各科平均分：')
by_gender = df.groupby('性别')[subjects].mean().round(2)
w(by_gender)
w('')
w('按班级+性别分组各科平均分：')
by_both = df.groupby(['班级', '性别'])[subjects].mean().round(2)
w(by_both)
w('')

# 观察结论
w('=' * 60)
w('五、观察结论')
w('=' * 60)

class_avg_total = df.groupby('班级')['总分'].mean()
top_class = class_avg_total.idxmax()
w(f'1. 从班级整体看，平均总分最高的班级为【{top_class}】（平均总分 {class_avg_total[top_class]:.1f}）；')

gender_avg_total = df.groupby('性别')['总分'].mean()
higher_gender = gender_avg_total.idxmax()
w(f'2. 从性别看，{higher_gender}生的平均总分更高（男生 {gender_avg_total["男"]:.1f} 分，女生 {gender_avg_total["女"]:.1f} 分）；')

gender_subj = df.groupby('性别')[subjects].mean()
for s in subjects:
    gmax = gender_subj[s].idxmax()
    w(f'   - 在{s}科目上，{gmax}生平均分较高（男 {gender_subj[s]["男"]:.2f}，女 {gender_subj[s]["女"]:.2f}）')

w('')
w('3. 从整体成绩看：')
for s in subjects:
    avg = df[s].mean()
    pr = pass_rate(df[s])
    er = excell_rate(df[s])
    w(f'   - {s}：平均 {avg:.2f}，及格率 {pr:.1f}%，优秀率 {er:.1f}%')
    if avg < 75:
        w(f'     该科目整体偏弱，平均分低于75分，需关注教学。')
    elif avg < 80:
        w(f'     该科目处于中等水平。')
    else:
        w(f'     该科目整体表现良好。')
w('')
w('4. 全部学生成绩无缺失，数据完整，可直接用于教学评估。')

# ---------- 保存 ----------
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('报告已生成：', OUT)

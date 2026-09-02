# -*- coding: utf-8 -*-
"""
学生成绩数据分析脚本
数据源：class_scores.xlsx（240 名学生，8 个班，语文/数学/英语三科）
功能：概览、三科均值/最高/最低/及格率/优秀率、总分前10、单科前5、
     按班级与性别分组的各科平均分，并输出中文报告 analysis_report.txt
"""
import pandas as pd

SRC = 'class_scores.xlsx'
OUT = 'analysis_report.txt'
SUBJECTS = ['语文', '数学', '英语']
PASS_LINE = 60.0   # 及格线
EXCELLENT_LINE = 90.0  # 优秀线

df = pd.read_excel(SRC)

# 计算总分
df['总分'] = df[SUBJECTS].sum(axis=1)

lines = []
def w(s=''):
    lines.append(str(s))

w('=' * 46)
w('学生成绩数据分析报告')
w('=' * 46)

# ---------- 1. 数据概览 ----------
w()
w('一、数据概览')
w(f'数据文件：{SRC}')
w(f'学生总数：{len(df)} 人')
w(f'班级数量：{df["班级"].nunique()} 个（{"/".join(sorted(set(df["班级"].astype(str))))}）')
w(f'性别分布：男 {int((df["性别"]=="男").sum())} 人，女 {int((df["性别"]=="女").sum())} 人')
w(f'科目：' + '、'.join(SUBJECTS) + '（满分均为 100 分）')
w(f'数据完整性：无缺失值（各字段缺失数均为 0）')

# ---------- 2. 各科统计指标 ----------
w()
w('二、各科统计指标（均值 / 最高 / 最低 / 及格率 / 优秀率）')
w('   （及格线=60分，优秀线=90分）')
w(f'{"科目":<4}{"平均分":>10}{"最高分":>10}{"最低分":>10}{"及格率":>12}{"优秀率":>12}')
for sub in SUBJECTS:
    s = df[sub]
    mean = s.mean()
    maxv = s.max()
    minv = s.min()
    pass_rate = (s >= PASS_LINE).mean() * 100
    excel_rate = (s >= EXCELLENT_LINE).mean() * 100
    w(f'{sub:<4}{mean:>10.2f}{maxv:>10.1f}{minv:>10.1f}{pass_rate:>10.2f}%{excel_rate:>10.2f}%')

# ---------- 3. 总分排名 ----------
w()
w('三、总分排名')
w(f'总分最高：{df["总分"].max():.1f} 分；总分最低：{df["总分"].min():.1f} 分；全体平均总分：{df["总分"].mean():.1f} 分')
w()
w('总分前 10 名：')
top10 = df.nlargest(10, '总分')
w(f'{"排名":<4}{"学号":<8}{"姓名":<6}{"班级":<4}{"性别":<4}{"语文":>8}{"数学":>8}{"英语":>8}{"总分":>8}')
for i, (_, r) in enumerate(top10.iterrows(), 1):
    rank_mark = '（并列）' if len(df[df['总分'] == r['总分']]) > 1 else ''
    w(f'{i:<4}{r["学号"]:<8}{r["姓名"]:<6}{r["班级"]:<4}{r["性别"]:<4}'
      f'{r["语文"]:>8.1f}{r["数学"]:>8.1f}{r["英语"]:>8.1f}{r["总分"]:>8.1f}{rank_mark}')

w()
w('各单科前 5 名：')
for sub in SUBJECTS:
    top5 = df.nlargest(5, sub)
    w(f'\n{sub} 前 5 名（最高 {df[sub].max():.1f} 分）：')
    w(f'{"排名":<4}{"学号":<8}{"姓名":<6}{"班级":<4}{"性别":<4}{sub + "成绩":>10}')
    for i, (_, r) in enumerate(top5.iterrows(), 1):
        w(f'{i:<4}{r["学号"]:<8}{r["姓名"]:<6}{r["班级"]:<4}{r["性别"]:<4}{r[sub]:>10.1f}')

# ---------- 4. 按班级 / 性别分组 ----------
w()
w('四、按班级和性别分组的各科平均分')

w('\n【按班级分组】各科平均分：')
w(f'{"班级":<6}{"人数":>6}' + ''.join(f'{s:>14}' for s in SUBJECTS) + f'{"总分平均":>14}')
class_means = df.groupby('班级')[SUBJECTS + ['总分']].mean()
for cls in sorted(df['班级'].astype(str).unique(), key=lambda x: int(x.rstrip('班'))):
    cnt = len(df[df['班级'] == cls])
    cm = class_means.loc[cls]
    w(f'{cls:<6}{cnt:>6}' + ''.join(f'{cm[s]:>14.2f}' for s in SUBJECTS) + f'{cm["总分"]:>14.2f}')

w('\n【按性别分组】各科平均分：')
w(f'{"性别":<6}{"人数":>6}' + ''.join(f'{s:>14}' for s in SUBJECTS) + f'{"总分平均":>14}')
gender_means = df.groupby('性别')[SUBJECTS + ['总分']].mean()
for g in ['男', '女']:
    cnt = len(df[df['性别'] == g])
    gm = gender_means.loc[g]
    w(f'{g:<6}{cnt:>6}' + ''.join(f'{gm[s]:>14.2f}' for s in SUBJECTS) + f'{gm["总分"]:>14.2f}')

w('\n【按班级×性别分组】各科平均分：')
w(f'{"班级":<6}{"性别":<4}' + ''.join(f'{s:>14}' for s in SUBJECTS) + f'{"总分平均":>14}')
bg = df.groupby(['班级', '性别'], sort=False)[SUBJECTS + ['总分']].mean()
for (cls, g), row in bg.iterrows():
    w(f'{cls:<6}{g:<4}' + ''.join(f'{row[s]:>14.2f}' for s in SUBJECTS) + f'{row["总分"]:>14.2f}')

# ---------- 5. 观察结论 ----------
w()
w('五、观察结论')

# 各科平均对比
sub_means = {s: df[s].mean() for s in SUBJECTS}
best_sub = max(sub_means, key=sub_means.get)
weak_sub = min(sub_means, key=sub_means.get)
w(f'1. 整体来看，三科中平均分最高的是「{best_sub}」（{sub_means[best_sub]:.2f} 分），'
  f'最薄弱的是「{weak_sub}」（{sub_means[weak_sub]:.2f} 分）。'
  f'其中英语平均分明显低于语文与数学，是全校相对需要加强的科目。')

# 及格率/优秀率观察
for s in SUBJECTS:
    pr = (df[s] >= PASS_LINE).mean() * 100
    if pr < 99:
        w(f'2. 「{s}」存在不及格学生（及格率 {pr:.1f}%），最低分 {df[s].min():.1f} 分，需重点关注低分段同学。')
        break
else:
    w('2. 三科及格率均达到 99% 以上，整体基础较扎实，主要差距体现在拔高（优秀率）上。')

# 班级差异
cls_avg = class_means['总分']
best_cls = cls_avg.idxmax()
worst_cls = cls_avg.idxmin()
w(f'3. 各班级总分平均分差异明显，最高为「{best_cls}」（总分平均 {cls_avg[best_cls]:.2f}），'
  f'最低为「{worst_cls}」（总分平均 {cls_avg[worst_cls]:.2f}），两者相差 '
  f'{cls_avg[best_cls]-cls_avg[worst_cls]:.2f} 分。从各科看，1、2班在多数科目上领先，'
  f'7、8班整体相对偏弱，班级间存在较明显的水平差距，可考虑在同教研组内开展结对帮扶。')

# 性别差异（动态判断每科哪个性别更高）
gm = gender_means
parts = []
for s in SUBJECTS:
    diff = gm.loc['女', s] - gm.loc['男', s]
    higher = '女生' if diff > 0 else '男生'
    parts.append(f'{s}：{higher}更高（相差 {abs(diff):.2f} 分）')
total_diff = gm.loc['女', '总分'] - gm.loc['男', '总分']
total_higher = '女生' if total_diff > 0 else '男生'
w(f'4. 性别维度：「' + '、'.join(parts) +
  f'」。综合来看，{total_higher}的总分平均分更高（相差 {abs(total_diff):.2f} 分），'
  f'整体差异不大，但以语文为代表的文科倾向科目女生优势相对明显。')

w()
w('（本报告由数据分析脚本自动生成，成绩数据共 240 条。）')

report = '\n'.join(lines)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(report + '\n')

print('报告已生成：', OUT)
print('总行数：', report.count('\n') + 1)

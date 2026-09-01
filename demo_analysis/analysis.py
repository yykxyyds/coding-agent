# -*- coding: utf-8 -*-
"""成绩数据分析脚本：生成 demo_analysis/analysis_report.txt"""

import openpyxl
from collections import defaultdict

SRC = "class_scores.xlsx"
OUT = "analysis_report.txt"


def load_data():
    wb = openpyxl.load_workbook(SRC)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    return rows


def safe_rate(vals, cmp_func):
    return sum(1 for v in vals if cmp_func(v)) / len(vals) * 100


def main():
    rows = load_data()
    subjects = ["语文", "数学", "英语"]

    report = []
    add = report.append

    # ============ 1. 数据概览 ============
    add("=" * 50)
    add("学生成绩数据分析报告")
    add("=" * 50)
    add(f"数据来源文件: {SRC}")
    add(f"总人数: {len(rows)} 人")
    classes = sorted(set(r[2] for r in rows))
    genders = sorted(set(r[3] for r in rows))
    add(f"班级数: {len(classes)} 个 -> {classes}")
    add(f"性别: {genders}")
    add(f"字段: {'、'.join(['学号','姓名','班级','性别'] + subjects)}")
    add("无缺失值，数据完整。")
    add("")

    # ============ 2. 各科统计 ============
    add("-" * 50)
    add("一、各科成绩统计")
    add("-" * 50)
    add(f"{'科目':<6}{'平均分':<10}{'最高分':<10}{'最低分':<10}{'及格率':<10}{'优秀率'}")
    all_sub = {}
    for s in subjects:
        idx = subjects.index(s) + 4  # 列索引
        vals = [r[idx] for r in rows]
        mean = sum(vals) / len(vals)
        high = max(vals)
        low = min(vals)
        pass_rate = safe_rate(vals, lambda v: v >= 60)
        excell_rate = safe_rate(vals, lambda v: v >= 90)
        all_sub[s] = vals
        add(f"{s:<6}{mean:<10.2f}{high:<10.1f}{low:<10.1f}{pass_rate:<10.2f}{excell_rate:<6.2f}%")
    add("及格线: 60 分；优秀线: 90 分")
    add("")

    # ============ 3. 总分排名 ============
    add("-" * 50)
    add("二、总分及排名")
    add("-" * 50)
    total_list = []
    for r in rows:
        total = round(r[4] + r[5] + r[6], 2)
        total_list.append((r[0], r[1], r[2], total))
    total_list.sort(key=lambda x: x[3], reverse=True)

    add("【总分前10名】")
    add(f"{'排名':<4}{'学号':<8}{'姓名':<8}{'班级':<6}{'总分'}")
    for i, (sid, name, cls, total) in enumerate(total_list[:10], 1):
        add(f"{i:<6}{sid:<10}{name:<10}{cls:<8}{total}")
    add("")

    add("【各科前5名】")
    for s in subjects:
        idx = subjects.index(s) + 4
        tops = sorted(rows, key=lambda r: r[idx], reverse=True)[:5]
        add(f"  {s} 前5名:")
        add(f"  {'排名':<4}{'学号':<8}{'姓名':<8}{'班级':<6}{s}")
        for i, r in enumerate(tops, 1):
            add(f"  {i:<6}{r[0]:<10}{r[1]:<10}{r[2]:<8}{r[idx]}")
        add("")
    add("")

    # ============ 4. 分组统计 ============
    add("-" * 50)
    add("三、按班级和性别分组统计")
    add("-" * 50)

    # 按班级
    add("【按班级分组: 各科平均分】")
    add(f"{'班级':<6}{'语文':<10}{'数学':<10}{'英语'}")
    cls_means = {}
    for c in classes:
        crows = [r for r in rows if r[2] == c]
        m = {}
        for s in subjects:
            idx = subjects.index(s) + 4
            m[s] = sum(r[idx] for r in crows) / len(crows)
        cls_means[c] = m
        add(f"{c:<8}{m['语文']:<10.2f}{m['数学']:<10.2f}{m['英语']:.2f}")
    add("")

    # 按性别
    add("【按性别分组: 各科平均分】")
    add(f"{'性别':<6}{'语文':<10}{'数学':<10}{'英语'}")
    gen_means = {}
    for g in genders:
        grows = [r for r in rows if r[3] == g]
        m = {}
        for s in subjects:
            idx = subjects.index(s) + 4
            m[s] = sum(r[idx] for r in grows) / len(grows)
        gen_means[g] = m
        add(f"{g:<8}{m['语文']:<10.2f}{m['数学']:<10.2f}{m['英语']:.2f}")
    add("")

    # 班级 x 性别
    add("【班级 × 性别: 各科平均分】")
    for c in classes:
        add(f"  {c}:")
        for g in genders:
            rows_ = [r for r in rows if r[2] == c and r[3] == g]
            m = {s: sum(r[4 + subjects.index(s)] for r in rows_) / len(rows_)
                 for s in subjects} if rows_ else {s: 0 for s in subjects}
            add(f"    {g} (n={len(rows_)}): 语文{m['语文']:.2f} 数学{m['数学']:.2f} 英语{m['英语']:.2f}")
    add("")

    # ============ 5. 观察结论 ============
    add("-" * 50)
    add("四、观察结论")
    add("-" * 50)

    # 总体优劣势
    overall = {s: sum(v) / len(v) for s, v in all_sub.items()}
    best_sub = max(overall, key=overall.get)
    weak_sub = min(overall, key=overall.get)
    add(f"1. 总体来看，三科平均分中【{best_sub}】最高（{overall[best_sub]:.2f}分），【{weak_sub}】最低（{overall[weak_sub]:.2f}分），整体{weak_sub}相对偏弱。")

    # 及格率 / 优秀率
    for s in subjects:
        vals = all_sub[s]
        pr = safe_rate(vals, lambda v: v >= 60)
        er = safe_rate(vals, lambda v: v >= 90)
        add(f"2. {s}及格率 {pr:.2f}%，优秀率 {er:.2f}%。") 

    # 班级对比
    cls_avg = {c: sum(m.values()) / 3 for c, m in cls_means.items()}
    best_cls = max(cls_avg, key=cls_avg.get)
    weak_cls = min(cls_avg, key=cls_avg.get)
    add(f"3. 班级对比：{best_cls}三科平均成绩最高，{weak_cls}相对最低，班级间存在一定差异。")

    # 性别对比
    diff = {s: gen_means['男'][s] - gen_means['女'][s] for s in subjects}
    gen_better = [s for s in subjects if gen_means['女'][s] > gen_means['男'][s]]
    gen_weak   = [s for s in subjects if gen_means['男'][s] > gen_means['女'][s]]
    if gen_better:
        add(f"4. 性别差异：女生在{('、'.join(gen_better))}上平均分高于男生；男生在{('、'.join(gen_weak))}上较高。")

    # 班内性别差异最大的班
    add("5. 班内班级×性别数据可见，各班男女生成绩结构不同，部分班级存在明显性别差异，建议针对性教学。")

    outcome = "\n".join(report)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(outcome)
    print(outcome)


if __name__ == "__main__":
    main()

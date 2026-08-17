# -*- coding: utf-8 -*-
"""评测报告生成：汇总各维度均分，输出 Markdown 与 CSV"""
import csv
import json
from datetime import datetime

import config
from scorer import DIMENSIONS


def _avg(nums):
    return round(sum(nums) / len(nums), 2) if nums else 0.0


def generate(scored, report_path="results/report.md", csv_path="results/report.csv",
             model_name=None):
    n = len(scored)
    dim_avg = {dim: _avg([s[dim] for s in scored]) for dim in DIMENSIONS}
    overall = round(sum(dim_avg.values()) / len(DIMENSIONS), 2)
    weakest = min(DIMENSIONS, key=lambda d: dim_avg[d])

    lines = [
        "# LLM 回复质量评测报告",
        "",
        f"- 被测模型：{model_name or config.ACTIVE['model']}",
        f"- 评测题数：{n}",
        f"- 评测日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 评分方式：LLM-as-Judge，temperature=0，五维评分（0-5）",
        "",
        "## 总览",
        "",
        "| 指标 | 得分 |",
        "| --- | --- |",
        f"| 综合均分 | **{overall}** |",
    ]
    for dim in DIMENSIONS:
        lines.append(f"| {dim} | {dim_avg[dim]} |")

    lines += ["", "## 逐题明细", "",
              "| 题号 | 准确性 | 相关性 | 完整性 | 流畅度 | 无幻觉 | 均分 | 主要问题 |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in scored:
        avg = _avg([s[d] for d in DIMENSIONS])
        lines.append(
            f"| {s['id']} | {s['accuracy']} | {s['relevance']} | {s['completeness']} | "
            f"{s['fluency']} | {s['hallucination']} | {avg} | {s.get('reason', '')} |")

    lines += ["", "## 结论与建议", "",
              f"- 最薄弱维度：**{weakest}**（{dim_avg[weakest]} 分），建议针对性优化提示词或补充该方向的评测用例",
              "- 单题均分低于 3 分的用例，建议人工复核后加入回归评测集，持续跟踪",
              "",
              "> 本报告由 llm-eval-tool 自动生成，用于模型质量对比与回归跟踪。"]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "question"] + DIMENSIONS + ["avg", "reason"])
        for s in scored:
            writer.writerow([s["id"], s["question"]] + [s[d] for d in DIMENSIONS]
                            + [_avg([s[d] for d in DIMENSIONS]), s.get("reason", "")])

    print(f"[report] Markdown 报告：{report_path}")
    print(f"[report] CSV 报告：{csv_path}")
    return lines

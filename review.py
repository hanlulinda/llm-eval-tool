# -*- coding: utf-8 -*-
"""人工复核模块：从评分结果中抽样，生成复核表，比对人工与 AI 评分一致性

对应 LLM 评测三大难点中的"人工复核兜底"：
自动化评分之外，抽样人工复核，用一致率校准 AI 评分的可靠性。

用法：
    python review.py                            # 默认抽 20%，生成 results/review_sheet.csv
    python review.py --sample 3                 # 指定抽 3 题
    python review.py --apply review_sheet.csv   # 回填人工评分后，生成一致性报告
"""
import argparse
import csv
import json
import os
import random
from datetime import datetime

from scorer import DIMENSIONS


def _avg(nums):
    nums = [float(n) for n in nums if n != ""]
    return round(sum(nums) / len(nums), 2) if nums else 0.0


def build_sheet(scored, n, sheet_path="results/review_sheet.csv"):
    """抽样生成人工复核表：含问题/回答/参考/AI 评分 + 空的人工评分列"""
    # 防护：若已有 sheet 且含人工打分（human_* 列有值），先备份，防止误覆盖丢数据
    if os.path.exists(sheet_path):
        try:
            with open(sheet_path, "r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    if row.get("human_accuracy"):
                        backup = sheet_path + ".bak"
                        with open(sheet_path, "rb") as src, open(backup, "wb") as dst:
                            dst.write(src.read())
                        print(f"[review] 检测到含人工打分的旧表，已备份为 {backup}")
                        break
        except Exception:
            pass
    items = scored if n >= len(scored) else random.sample(scored, n)
    # 补充参考回答（从评测集读取，供人工判断准确性）
    ref_by_id = {}
    try:
        with open("eval_set.json", "r", encoding="utf-8") as f:
            ref_by_id = {it["id"]: it.get("reference", "") for it in json.load(f)}
    except Exception:
        pass
    with open(sheet_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "question", "answer", "reference",
                         "ai_accuracy", "ai_relevance", "ai_completeness",
                         "ai_fluency", "ai_hallucination", "ai_reason",
                         "human_accuracy", "human_relevance", "human_completeness",
                         "human_fluency", "human_hallucination", "human_reason"])
        for it in items:
            reference = ref_by_id.get(it["id"], it.get("reference", ""))
            writer.writerow([it["id"], it["question"], it["answer"], reference,
                             it["accuracy"], it["relevance"], it["completeness"],
                             it["fluency"], it["hallucination"], it.get("reason", ""),
                             "", "", "", "", "", ""])
    print(f"[review] 复核表已生成：{sheet_path}")
    print(f"[review] 请用 Excel/WPS 打开，填写 human_* 列（0-5 分），保存后执行 --apply")


def apply_review(sheet_path, scored, report_path="results/review_report.md"):
    """读取已填写的复核表，比对人工与 AI 评分，生成一致性报告"""
    rows = []
    with open(sheet_path, "r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    total, agree_count, disagree = 0, 0, []
    md = ["# 人工复核一致性报告", "",
          f"- 复核题数：{len(rows)}",
          f"- 判定标准：AI 均分与人工均分偏差 ≤1 分视为一致",
          f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
          "", "| 题号 | AI均分 | 人工均分 | 偏差 | 是否一致 | 人工备注 |",
          "| --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        if not r.get("human_accuracy"):
            continue
        total += 1
        ai_avg = _avg([r.get(f"ai_{d}") for d in DIMENSIONS])
        hu_avg = _avg([r.get(f"human_{d}") for d in DIMENSIONS])
        diff = round(abs(ai_avg - hu_avg), 2)
        agree = diff <= 1.0
        if agree:
            agree_count += 1
        else:
            disagree.append(r["id"])
        md.append(f"| {r['id']} | {ai_avg} | {hu_avg} | {diff} | {'✅' if agree else '❌'} | "
                  f"{r.get('human_reason', '')} |")

    rate = round(agree_count / total * 100, 1) if total else 0.0
    md += ["", "## 结论", "",
           f"- 人工与 AI 评分一致率：**{rate}%**（{agree_count}/{total}）",
           f"- 不一致题目：{disagree if disagree else '无'}",
           "",
           "> 一致率低（如 <80%）说明 AI 评分标准需要校准：细化评分档位定义、"
           "补充 few-shot 示例，或对争议题人工修订评分标准后重新评测。",
           "",
           "> 本报告由 llm-eval-tool 人工复核模块生成。"]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"[review] 一致性报告已生成：{report_path}（一致率 {rate}%）")
    return rate


def main():
    parser = argparse.ArgumentParser(description="LLM 评测人工复核")
    parser.add_argument("--sample", type=int, default=None,
                        help="抽样题数（默认取总题数的 20%）")
    parser.add_argument("--apply", metavar="SHEET_CSV",
                        help="回填人工评分后的复核表路径，生成一致性报告")
    args = parser.parse_args()

    scores_path = "results/scores.json"
    if args.apply:
        if not os.path.exists(scores_path):
            print(f"[review] 未找到 {scores_path}，请先运行 python main.py")
            return
        with open(scores_path, "r", encoding="utf-8") as f:
            scored = json.load(f)
        apply_review(args.apply, scored)
        return

    if not os.path.exists(scores_path):
        print(f"[review] 未找到 {scores_path}，请先运行 python main.py")
        return
    with open(scores_path, "r", encoding="utf-8") as f:
        scored = json.load(f)

    n = args.sample if args.sample else max(1, round(len(scored) * 0.2))
    build_sheet(scored, n)


if __name__ == "__main__":
    main()

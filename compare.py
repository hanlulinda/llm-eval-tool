# -*- coding: utf-8 -*-
"""双模型对比（A/B）：同一评测集跑两个模型，生成对比报告

默认对比 DeepSeek 的两个模型（同一个 Key，0 成本）：
- deepseek-chat（通用对话）
- deepseek-reasoner（推理模型）

用法：
    python compare.py                  # 真实对比（默认：deepseek-chat vs deepseek-reasoner）
    python compare.py --temps 0.7 0    # 同一模型对比不同 temperature（一致性/稳定性观察）
    python compare.py --mock           # 模拟对比（无 Key 演示全流程）

说明：
- 两个模型用同一个 Judge（deepseek-chat）打分，保证评分口径一致、可比
- 想换其他模型（如通义千问），在下方 MODELS 里增删即可
"""
import argparse
import json
import os

import config
import evaluator
import report as report_mod
import scorer

OUT_DIR = "results/compare"

# 对比模型列表：默认 DeepSeek 同 Key 两个模型（reasoner 不支持 temperature，置 None）
MODELS = [
    {
        "name": "deepseek-chat（通用）",
        "key": config.DEEPSEEK_API_KEY,
        "base_url": config.DEEPSEEK_BASE_URL,
        "model": config.DEEPSEEK_MODEL,
        "temperature": 0.7,
    },
    {
        "name": "deepseek-reasoner（推理）",
        "key": config.DEEPSEEK_API_KEY,
        "base_url": config.DEEPSEEK_BASE_URL,
        "model": "deepseek-reasoner",
        "temperature": None,
    },
]

# 统一裁判（Judge）：始终用通用模型打分，保证两模型评分口径一致
JUDGE_CFG = {
    "api_key": config.DEEPSEEK_API_KEY,
    "base_url": config.DEEPSEEK_BASE_URL,
    "model": config.DEEPSEEK_MODEL,
}


def main():
    parser = argparse.ArgumentParser(description="双模型对比评测")
    parser.add_argument("--mock", action="store_true", help="模拟模式：不调用真实 API")
    parser.add_argument("--temps", nargs="+", type=float,
                        help="同一模型对比不同 temperature，如 --temps 0.7 0")
    args = parser.parse_args()

    models = MODELS
    if args.temps:
        m = config.ACTIVE
        models = [{"name": f"{m['model']} (t={t})", "key": m["api_key"],
                   "base_url": m["base_url"], "model": m["model"], "temperature": t}
                  for t in args.temps]
        print(f"[compare] 温度对比模式：{' vs '.join(x['name'] for x in models)}")

    # mock 模式输出到 results/compare/mock/，绝不覆盖真实对比产物（防污染）
    out_dir = f"{OUT_DIR}/mock" if args.mock else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    with open("eval_set.json", "r", encoding="utf-8") as f:
        eval_set = json.load(f)
    print(f"[compare] 评测集：{len(eval_set)} 题" + ("（mock 模式，产物在 results/compare/mock/）" if args.mock else ""))
    print(f"[compare] 对比对象：{' vs '.join(m['name'] for m in models)}")

    all_scores = {}
    for m in models:
        tag = f"[{m['name']}]"
        model_cfg = {"api_key": m["key"], "base_url": m["base_url"],
                     "model": m["model"], "temperature": m.get("temperature", 0.7)}
        if args.mock:
            answers = evaluator.run_mock(eval_set,
                                         output_path=f"{out_dir}/{m['model']}_t{m.get('temperature', 'x')}_answers.json")
            scored = scorer.run(eval_set, answers,
                                output_path=f"{out_dir}/{m['model']}_t{m.get('temperature', 'x')}_scores.json",
                                mock=True, tag=tag)
        else:
            answers = evaluator.run(eval_set,
                                    output_path=f"{out_dir}/{m['model']}_t{m.get('temperature', 'x')}_answers.json",
                                    cfg=model_cfg, tag=tag)
            scored = scorer.run(eval_set, answers,
                                output_path=f"{out_dir}/{m['model']}_t{m.get('temperature', 'x')}_scores.json",
                                cfg=JUDGE_CFG, tag=tag)
        report_mod.generate(scored,
                            report_path=f"{out_dir}/{m['model']}_t{m.get('temperature', 'x')}_report.md",
                            csv_path=f"{out_dir}/{m['model']}_t{m.get('temperature', 'x')}_report.csv",
                            model_name=m["name"])
        all_scores[m["name"]] = scored

    if args.temps:
        advice = ("- 结论：temperature 越低回答越稳定可复现，越高越多样；"
                  "若追求稳定（如评分、配置生成）建议 t=0；"
                  "如需多样性（如创意内容）可适当调高。\n"
                  "- 更严谨的一致性评测：同一温度多次采样（如 3 次），统计回答/评分的方差。")
    else:
        advice = ("- 结论：结合业务场景选择：推理类问题（分析/计算）选推理模型，"
                  "对话与内容生成场景选通用模型")
    build_compare_report(all_scores, advice, out_dir)


def _avg(scored, dim):
    vals = [s[dim] for s in scored]
    return round(sum(vals) / len(vals), 2)


def build_compare_report(all_scores, advice=None, out_dir="results/compare"):
    """生成对比报告：各维度均分对比 + 逐题分数对比；advice 为结论建议文本"""
    names = list(all_scores.keys())
    n = len(all_scores[names[0]])
    lines = ["# 双模型对比评测报告", "",
             f"- 评测题数：{n}",
             f"- 对比对象：{' vs '.join(names)}",
             "- 评分方式：统一 Judge（deepseek-chat）五维评分，temperature=0",
             "", "## 维度均分对比", "",
             "| 维度 | " + " | ".join(names) + " | 差值 |",
             "| --- | " + " | ".join(["---"] * len(names)) + " | --- |"]

    for dim in scorer.DIMENSIONS:
        vals = [_avg(all_scores[name], dim) for name in names]
        diff = round(vals[0] - vals[1], 2)
        lines.append(f"| {dim} | " + " | ".join(str(v) for v in vals) + f" | {diff:+.2f} |")

    overalls = [round(sum(_avg(all_scores[name], d) for d in scorer.DIMENSIONS)
                      / len(scorer.DIMENSIONS), 2) for name in names]
    lines.append(f"| 综合均分 | " + " | ".join(str(v) for v in overalls)
                 + f" | {round(overalls[0] - overalls[1], 2):+.2f} |")

    lines += ["", "## 逐题对比", "",
              "| 题号 | " + " | ".join(names) + " | 优势方 |",
              "| --- | " + " | ".join(["---"] * len(names)) + " | --- |"]
    for i in range(n):
        qid = all_scores[names[0]][i]["id"]
        avgs = []
        for name in names:
            by_id = {s["id"]: s for s in all_scores[name]}
            s = by_id[qid]
            avgs.append(round(sum(s[d] for d in scorer.DIMENSIONS) / len(scorer.DIMENSIONS), 2))
        winner = names[0] if avgs[0] > avgs[1] else (names[1] if avgs[1] > avgs[0] else "持平")
        lines.append(f"| {qid} | " + " | ".join(str(a) for a in avgs) + f" | {winner} |")

    win = "领先" if overalls[0] > overalls[1] else ("落后" if overalls[0] < overalls[1] else "持平")
    lines += ["", "## 结论", "",
              f"- 综合均分：{names[0]} {win} {abs(overalls[0] - overalls[1]):.2f} 分"]
    if advice:
        lines += advice.split("\n")
    lines += ["", "> 本报告由 llm-eval-tool 对比评测模块生成（同一评测集，评分口径一致，可比）。"]

    path = f"{out_dir}/compare_report.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[compare] 对比报告已生成：{path}")


if __name__ == "__main__":
    main()

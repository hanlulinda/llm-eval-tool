# -*- coding: utf-8 -*-
"""LLM 回复质量评测工具 v1 —— 入口

用法：
    python main.py                  # 全流程：生成回答 → 评分 → 出报告
    python main.py --skip-generate  # 复用已生成的回答，只重新评分出报告
    python main.py --mock           # 模拟模式：无 API Key 也能跑通全流程（结果仅供演示）
"""
import argparse
import json
import os

import evaluator
import report as report_mod
import scorer


def load_eval_set(path="eval_set.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="LLM 回复质量评测工具")
    parser.add_argument("--skip-generate", action="store_true",
                        help="复用 results/answers.json，跳过回答生成")
    parser.add_argument("--mock", action="store_true",
                        help="模拟模式：不调用真实 API，用模拟数据跑通全流程")
    args = parser.parse_args()

    os.makedirs("results", exist_ok=True)
    eval_set = load_eval_set()
    print(f"[main] 评测集加载：{len(eval_set)} 题")

    if args.mock:
        answers = evaluator.run_mock(eval_set)
    elif args.skip_generate and os.path.exists("results/answers.json"):
        with open("results/answers.json", "r", encoding="utf-8") as f:
            answers = json.load(f)
        print("[main] 复用已有回答")
    else:
        answers = evaluator.run(eval_set)

    scored = scorer.run(eval_set, answers, mock=args.mock)
    report_mod.generate(scored)
    print("[main] 全流程完成 ✅")


if __name__ == "__main__":
    main()

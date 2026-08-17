# -*- coding: utf-8 -*-
"""评测集执行器：调用被测 LLM，逐题生成回答"""
import json
import time

import config


def get_client(cfg=None):
    """创建 OpenAI 兼容客户端（惰性导入：mock 模式不依赖 openai 包）
    cfg 为空时使用 config.ACTIVE；传入其他模型配置（如对比评测）时使用该配置"""
    from openai import OpenAI
    cfg = cfg or config.ACTIVE
    return OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])


def ask_llm(client, question, model=None, temperature=0.7, max_tokens=1024, retries=3):
    """调用被测模型回答单题，失败自动重试；temperature=None 时不传该参数（兼容 reasoner 模型）"""
    model = model or config.ACTIVE["model"]
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": question}],
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    for attempt in range(1, retries + 1):
        try:
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            print(f"[evaluator] 第 {attempt}/{retries} 次调用失败：{exc}")
            time.sleep(2)
    return "[ERROR] 模型调用失败"


def run(eval_set, output_path="results/answers.json", cfg=None, tag=""):
    """对评测集逐题生成回答并落盘；cfg 可指定其他模型配置（对比评测用），tag 用于日志标识"""
    client = get_client(cfg)
    cfg = cfg or config.ACTIVE
    model = cfg["model"]
    temperature = cfg.get("temperature", 0.7)
    answers = []
    for idx, item in enumerate(eval_set, 1):
        print(f"[evaluator]{tag} 评测第 {idx}/{len(eval_set)} 题：{item['question'][:30]}...")
        answer = ask_llm(client, item["question"], model=model, temperature=temperature)
        answers.append({
            "id": item["id"],
            "question": item["question"],
            "answer": answer,
        })
        time.sleep(0.5)  # 限流保护
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(answers, f, ensure_ascii=False, indent=2)
    print(f"[evaluator] 回答已保存：{output_path}")
    return answers


# 模拟回答池：mock 模式下循环使用，用于没有 API Key 时先跑通全流程
MOCK_ANSWERS = [
    "商品详情页主要展示商品规格、价格、评价与促销信息，用户可查看参数并加入购物车。",
    "该活动支持满减与加价购，活动期内下单可享受对应优惠，具体以结算页展示为准。",
    "接口自动化测试应覆盖正常流程、边界值与异常场景，并保证测试数据可复用、可隔离。",
    "埋点验证需对照事件手册核对事件名与参数，确保上报数据准确完整。",
]


def run_mock(eval_set, output_path="results/answers.json"):
    """模拟模式：不调用真实 API，用预设回答跑通全流程"""
    answers = []
    for idx, item in enumerate(eval_set, 1):
        answer = MOCK_ANSWERS[idx % len(MOCK_ANSWERS)]
        answers.append({"id": item["id"], "question": item["question"], "answer": answer})
        print(f"[evaluator][mock] 第 {idx}/{len(eval_set)} 题（模拟回答）")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(answers, f, ensure_ascii=False, indent=2)
    print(f"[evaluator] 模拟回答已保存：{output_path}")
    return answers

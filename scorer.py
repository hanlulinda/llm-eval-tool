# -*- coding: utf-8 -*-
"""LLM-as-Judge 评分器：对回答逐题多维打分"""
import json
import re
import time

from prompts import JUDGE_SYSTEM, JUDGE_USER_NO_REF, JUDGE_USER_TEMPLATE

DIMENSIONS = ["accuracy", "relevance", "completeness", "fluency", "hallucination"]


def get_active_config():
    """仅在真实 API 评分时加载含密钥的运行时配置。"""
    import config
    return config.ACTIVE


def get_client(cfg=None):
    """创建用于调用 Judge 模型的 OpenAI 兼容客户端（惰性导入）"""
    from openai import OpenAI
    cfg = cfg or get_active_config()
    return OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])


def extract_json(text):
    """从模型输出中稳健解析 JSON（容忍 ```json 代码块包裹等）"""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.M)
    text = re.sub(r"\s*```$", "", text, flags=re.M)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"评分输出无法解析为 JSON：{text[:200]}")
    return json.loads(text[start:end + 1])


def judge_one(client, item, answer, model=None, retries=3):
    """对单题回答调用 Judge 打分，返回 {维度: 分数, reason}"""
    model = model or get_active_config()["model"]
    reference = item.get("reference", "").strip()
    if reference:
        user_prompt = JUDGE_USER_TEMPLATE.format(
            question=item["question"], answer=answer, reference=reference)
    else:
        user_prompt = JUDGE_USER_NO_REF.format(question=item["question"], answer=answer)

    for attempt in range(1, retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,  # 评分必须稳定可复现
            )
            data = extract_json(resp.choices[0].message.content.strip())
            for dim in DIMENSIONS:  # 兜底：缺失维度记 0 并告警
                if dim not in data:
                    print(f"[scorer] 警告：{item['id']} 缺少维度 {dim}")
                    data[dim] = 0
            data["reason"] = str(data.get("reason", ""))[:100]
            return data
        except Exception as exc:
            print(f"[scorer] 第 {attempt}/{retries} 次评分失败：{exc}")
            time.sleep(2)
    return {dim: 0 for dim in DIMENSIONS} | {"reason": "评分失败"}


def judge_one_mock(item, answer):
    """模拟评分：以题目 id 作随机种子，同一题多次运行结果一致（可复现）"""
    import random
    rng = random.Random(item["id"])
    scores = {dim: rng.randint(3, 5) for dim in DIMENSIONS}
    scores["reason"] = "模拟评分（mock 模式，未调用真实模型，仅用于流程演示）"
    return scores


def run(eval_set, answers, output_path="results/scores.json", mock=False, cfg=None, tag=""):
    """逐题评分：按 id 对齐回答与评测集；mock=True 时使用模拟评分；cfg 指定 Judge 模型配置"""
    by_id = {a["id"]: a for a in answers}
    judge_cfg = cfg or (None if mock else get_active_config())
    client = None
    scored = []
    for idx, item in enumerate(eval_set, 1):
        answer = by_id.get(item["id"], {}).get("answer", "[ERROR] 无回答")
        print(f"[scorer]{tag} 评分第 {idx}/{len(eval_set)} 题：{item['id']}"
              + ("（mock）" if mock else ""))
        if mock:
            scores = judge_one_mock(item, answer)
        else:
            if client is None:
                client = get_client(judge_cfg)
            scores = judge_one(client, item, answer, model=judge_cfg["model"])
        scored.append({
            "id": item["id"],
            "question": item["question"],
            "answer": answer,
            **scores,
        })
        time.sleep(0.5)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=2)
    print(f"[scorer] 评分已保存：{output_path}")
    return scored

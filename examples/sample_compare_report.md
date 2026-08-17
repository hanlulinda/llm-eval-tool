# 双模型对比评测报告

- 评测题数：10
- 对比对象：deepseek-chat（通用） vs deepseek-reasoner（推理）
- 评分方式：统一 Judge（deepseek-chat）五维评分，temperature=0

## 维度均分对比

| 维度 | deepseek-chat（通用） | deepseek-reasoner（推理） | 差值 |
| --- | --- | --- | --- |
| accuracy | 4.5 | 4.1 | +0.40 |
| relevance | 5.0 | 4.6 | +0.40 |
| completeness | 4.7 | 4.1 | +0.60 |
| fluency | 4.7 | 4.3 | +0.40 |
| hallucination | 4.5 | 4.2 | +0.30 |
| 综合均分 | 4.68 | 4.26 | +0.42 |

## 逐题对比

| 题号 | deepseek-chat（通用） | deepseek-reasoner（推理） | 优势方 |
| --- | --- | --- | --- |
| e1 | 4.6 | 4.2 | deepseek-chat（通用） |
| e2 | 4.2 | 4.2 | 持平 |
| e3 | 5.0 | 5.0 | 持平 |
| e4 | 4.2 | 4.0 | deepseek-chat（通用） |
| e5 | 5.0 | 5.0 | 持平 |
| e6 | 5.0 | 5.0 | 持平 |
| e7 | 4.2 | 4.6 | deepseek-reasoner（推理） |
| e8 | 5.0 | 1.0 | deepseek-chat（通用） |
| e9 | 5.0 | 5.0 | 持平 |
| e10 | 4.6 | 4.6 | 持平 |

## 结论

- 综合均分：deepseek-chat（通用） 领先 0.42 分
- 结论：结合业务场景选择：推理类问题（分析/计算）选推理模型，对话与内容生成场景选通用模型

> 本报告由 llm-eval-tool 对比评测模块生成（同一评测集，评分口径一致，可比）。
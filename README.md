# llm-eval-tool — LLM 回复质量自动评测工具

[![CI](https://github.com/hanlulinda/llm-eval-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/hanlulinda/llm-eval-tool/actions/workflows/ci.yml)

对被测大模型的回答进行**多维自动评分**并生成评测报告，属于"AI 测试 / 大模型评测"方向的实战项目。

## 为什么做这个项目

AI 测试工程师的核心能力之一就是**评测体系**：构造评测集、设计评测指标、实现自动化评测与回归（这正是多家武汉 AI 测试岗位 JD 的要求）。本项目用最小可运行的方式实现这套体系：

- 评测集：`eval_set.json`（覆盖电商 / 软件测试 / 大模型 / 技术域，10 题起步）
- 评分：LLM-as-Judge（用大模型当裁判），五维评分：准确性 / 相关性 / 完整性 / 流畅度 / 无幻觉度
- 报告：自动生成 Markdown + CSV 报告，支持逐题明细与薄弱维度分析
- 可复现：Judge 调用 `temperature=0`，同题多次评分结果稳定

## 快速开始

```bash
cd llm-eval-tool
pip install -r requirements.txt

# 0. 没 API Key？先跑模拟模式，全流程立刻可见（结果仅供演示）
python main.py --mock

# 1. 获取 API Key（10 元足够跑完本项目）
#    DeepSeek: https://platform.deepseek.com
#    通义千问: https://bailian.console.aliyun.com

# 2. 配置 config.py 中的 ACTIVE（默认 DeepSeek）

# 3. 运行
python main.py                  # 全流程：生成回答 → 评分 → 出报告
python main.py --skip-generate  # 复用已回答，重新评分出报告
```

产物在 `results/` 目录：`answers.json`（原始回答）、`scores.json`（逐题评分）、`report.md`（报告）、`report.csv`（表格数据）。
> 说明：`--mock` 模式的产物在 `results/mock/` 独立目录（不污染真实评测数据）；`compare.py --mock` 在 `results/compare/mock/`。

## 真实评测结果（2026-08-20，DeepSeek 真实 API）

**主评测（15 题）**：综合均分 **4.6 / 5**，最薄弱维度 accuracy 与 hallucination（4.33）→ 提示补该方向评测用例（薄弱维度分析）

**人工复核（3 题抽样）**：AI 与人工一致率 **66.7%**（2/3），不一致题 e3（AI 4.8 vs 人工 3.0）→ 触发评分标准校准闭环

**双模型对比（15 题，统一 Judge）**：deepseek-chat 综合 **4.56** vs deepseek-reasoner **4.0**（+0.56）；reasoner 在工程技术题（用例生成/测试数据设计/MySQL索引）拿低分、但在电商客服题反超 → 结论：结合业务场景选型

（样例报告见 `examples/`：sample_report.md / sample_review_report.md / sample_compare_report.md）

## 人工复核（对应 LLM 评测难点：人工兜底）

自动化评分之外，抽样人工复核，用**一致率**校准 AI 评分的可靠性：

```bash
python review.py                            # 默认抽 20%，生成 results/review_sheet.csv
python review.py --sample 3                 # 指定抽 3 题
# 用 Excel/WPS 打开复核表，填 human_* 列（0-5 分），保存
python review.py --apply results/review_sheet.csv  # 生成一致性报告 review_report.md
```

一致率低（<80%）说明 AI 评分标准需要校准：细化评分档位、补充 few-shot 示例、人工修订争议题标准后重新评测。

## 双模型对比（A/B 选型）

同一评测集跑两个模型，用**同一个 Judge** 打分（口径一致、可比），生成对比报告：

```bash
python compare.py            # 真实对比（默认：deepseek-chat vs deepseek-reasoner，同一个 Key，0 成本）
python compare.py --mock     # 模拟演示
```

- 产物在 `results/compare/`：每个模型的回答/评分/报告 + `compare_report.md`（维度均分对比 + 逐题对比 + 结论）
- 想换模型（如通义千问），改 `compare.py` 里的 `MODELS` 列表即可
- 注意：`deepseek-reasoner` 不支持 temperature 参数，配置里已置 `None` 自动跳过

## 如何落地到实际工作场景

这个框架是"评测平台"的最小实现。**代码框架是一次性投入，日常维护的是评测集（case）和评分标准（prompt）**，落地关键是理解业务：

| 场景 | 怎么用 |
|---|---|
| 模型迭代回归 | 模型/提示词改动后重跑同一评测集，对比均分防止质量回退 |
| 模型选型（A/B） | 同一评测集跑两个模型，出对比报告辅助决策 |
| 提示词调优验证 | 用分数说话，代替"我觉得效果变好了" |
| 上线质量监控 | 抽样线上真实问题回流评测集，跟踪质量趋势 |

落地五步：
1. **对齐业务标准**：和产品/算法确认"什么叫回答好"，翻译成评测维度（业务不同维度不同——如电商客服更关注"是否包含价格/库存信息"，而不只是通用五维）
2. **构造评测集**：从真实用户问题抽样，标注参考回答（这是最重要的投入）
3. **跑评测 + 人工复核**：用一致率验证 AI 评分可信，校准评分标准
4. **沉淀回归集**：每次迭代重跑，出报告同步团队
5. **平台化**：日常只维护 case 和 prompt，代码框架不动

> 面试话术："给我一个 AI 功能，我可以用这套框架在一两周内搭起它的质量评测体系——先对齐业务标准，构造评测集，跑通评测和人工复核，再沉淀成每次迭代都跑的回归。"

## 目录结构

```
llm-eval-tool/
├── config.py       # API 配置（DeepSeek / 通义千问一键切换）
├── prompts.py      # 提示词模板（Judge 评分标准 + 输出约束）
├── evaluator.py    # 评测集执行器：调用被测模型生成回答（含 mock 模式）
├── scorer.py       # LLM-as-Judge 评分器：五维打分（含 mock 评分）
├── review.py       # 人工复核：抽样复核表 + 人工/AI 一致率报告
├── report.py       # 报告生成：汇总均分 + Markdown/CSV
├── main.py         # 入口（--mock / --skip-generate）
├── eval_set.json   # 评测集（可自由扩展）
└── requirements.txt
```

## 如何扩展评测集

1. **覆盖场景**：业务域（电商 / 客服 / 金融）+ 通用能力（推理 / 多语言 / 长文本）+ 边界与对抗用例（诱导幻觉、模糊提问）
2. **标注参考回答**：每条用例给出权威参考，用于 accuracy 判定；开放式问题可不填 reference
3. **回归跟踪**：模型升级或提示词改动后重跑同一评测集，对比均分变化——这就是"自动化评测回归"

## 扩展路线

- [x] **人工复核**：抽样复核表 + 人工/AI 一致率报告（review.py）
- [x] **无 Key 演示**：mock 模式跑通全流程（main.py --mock）
- [x] **双模型对比（A/B）**：同一评测集跑两个模型，统一 Judge，生成对比报告（compare.py）
- [ ] **一致性评测**：同一题多次采样（temperature>0），统计方差衡量稳定性
- [ ] **AI 辅助测试用例生成**：用大模型根据需求生成测试用例，人工审核后入库
- [ ] **接入 CI**：把评测脚本挂到流水线，模型发版自动跑回归

## 面试可讲的点

- **提示词工程**：角色设定、评分标准细化、JSON 输出约束、温度控制
- **LLM-as-Judge 的局限与缓解**：裁判模型可能偏好自身风格（self-bias）、评分漂移；缓解手段：评分标准细化、抽样人工复核、多裁判投票
- **评测体系方法论**：评测集构造、指标设计、回归自动化——直接对应测开 JD 中"构建 AI 评测体系"的要求

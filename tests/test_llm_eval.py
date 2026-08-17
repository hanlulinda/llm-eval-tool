# -*- coding: utf-8 -*-
"""llm-eval-tool 单元测试（CI 中执行，不消耗 API Key）

覆盖：JSON 解析容错、mock 评分可复现性、评分范围
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scorer import DIMENSIONS, extract_json, judge_one_mock


def test_dimensions():
    assert DIMENSIONS == ["accuracy", "relevance", "completeness", "fluency", "hallucination"]


def test_extract_json_plain():
    assert extract_json('{"accuracy": 4, "relevance": 5}') == {"accuracy": 4, "relevance": 5}


def test_extract_json_with_fence():
    """容忍 ```json 代码块包裹"""
    text = '```json\n{"accuracy": 4, "relevance": 5}\n```'
    assert extract_json(text) == {"accuracy": 4, "relevance": 5}


def test_extract_json_extra_text():
    """容忍评分理由等多余文本"""
    text = '好的，评分如下：{"accuracy": 4, "reason": "回答完整"}'
    data = extract_json(text)
    assert data["accuracy"] == 4
    assert data["reason"] == "回答完整"


def test_mock_score_reproducible():
    """同一题多次 mock 评分结果一致（可复现）"""
    item = {"id": "e1"}
    assert judge_one_mock(item, "answer") == judge_one_mock(item, "answer")


def test_mock_score_range():
    """评分在 0-5 范围内"""
    s = judge_one_mock({"id": "e9"}, "x")
    for dim in DIMENSIONS:
        assert 0 <= s[dim] <= 5


def test_scorer_imports_without_runtime_config(tmp_path):
    """CI 不提供含 API Key 的 config.py 时，纯评分工具仍应可导入。"""
    root = Path(__file__).resolve().parents[1]
    for module in ("scorer.py", "prompts.py"):
        shutil.copy(root / module, tmp_path / module)

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", "import scorer"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

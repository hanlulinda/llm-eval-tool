# -*- coding: utf-8 -*-
"""API 配置模板（提交到 Git 的版本）

用法：
    1. 复制本文件为 config.py：cp config.example.py config.py
    2. 在 config.py 中填入你的真实 API Key
    3. config.py 已被 .gitignore 排除，不会提交到 Git
"""
import os

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-在这里填你的key")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

QWEN_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-在这里填你的key")
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen-plus"

# 当前生效的模型配置：切换被测模型时改这里
ACTIVE = {
    "api_key": DEEPSEEK_API_KEY,
    "base_url": DEEPSEEK_BASE_URL,
    "model": DEEPSEEK_MODEL,
}

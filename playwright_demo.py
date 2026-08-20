# -*- coding: utf-8 -*-
"""Playwright 最小示例：打开页面 → 获取标题 → 智能等待 → 截图

用法：
    .venv/bin/python playwright_demo.py

说明：这是"我实际跑过 Playwright"的最小证据，面试可提。
"""
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    # 启动浏览器（headless=True 无头模式，不弹窗口）
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 打开页面
    page.goto("https://example.com")

    # 核心 API 演示
    print("页面标题:", page.title())            # 获取标题

    # 智能等待：等元素可见（代替 time.sleep）
    expect(page.locator("h1")).to_be_visible()
    print("h1 文本:", page.locator("h1").inner_text())

    # 语义化定位器演示（get_by_role）
    link = page.get_by_role("link", name="More information...")
    print("链接可见:", link.is_visible())

    # 截图（证据）
    page.screenshot(path="results/playwright_demo.png")
    print("截图已保存: results/playwright_demo.png")

    browser.close()
    print("✅ Playwright 最小示例跑通")

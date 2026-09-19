#!/usr/bin/env python3
"""TOC navigation and current-subsection regression.

Run: uv run --with playwright python site/tools/check_navigation.py BASE_URL
"""

import asyncio
import sys

from playwright.async_api import async_playwright


async def ready(page, url):
    await page.goto(url)
    await page.evaluate("window.MathJax?.startup?.promise")
    await page.evaluate("document.fonts.ready")


async def current(page, anchor):
    await page.wait_for_function("""anchor => {
        const links = [...document.querySelectorAll(
            '.ltx_page_navbar a[aria-current="location"]')];
        return anchor ? links.length === 1 && links[0].hash === anchor
            : links.length === 0;
    }""", arg=anchor)
    assert await page.locator('.ltx_page_navbar a[href^="#"]').evaluate_all("""
        links => links.every(link => getComputedStyle(link).fontWeight ===
            (link.hasAttribute('aria-current') ? '600' : '400'))
    """)


async def check(page, base, path):
    url = f"{base}/{path}"
    await page.set_viewport_size({"width": 1440, "height": 900})
    await ready(page, url)
    sidebar = page.locator(".ltx_page_navbar")
    assert await sidebar.is_visible()
    anchors = await sidebar.locator('a[href^="#"]').evaluate_all(
        "links => links.map(link => link.hash)")
    assert len(anchors) >= 4, anchors
    await current(page, None)
    for anchor in (anchors[0], anchors[2], anchors[1], anchors[-1]):
        await page.evaluate("""hash => document.getElementById(
            decodeURIComponent(hash.slice(1))).scrollIntoView()""", anchor)
        await current(page, anchor)
    await page.evaluate("scrollTo(0, document.documentElement.scrollHeight)")
    await current(page, anchors[-1])
    await page.evaluate("scrollTo(0, 0)")
    await current(page, None)
    await ready(page, f"{url}{anchors[1]}")
    await current(page, anchors[1])
    await page.set_viewport_size({"width": 768, "height": 1024})
    assert not await sidebar.is_visible()
    await page.evaluate("scrollTo(0, 0)")
    await page.set_viewport_size({"width": 1440, "height": 900})
    await current(page, None)
    await page.set_viewport_size({"width": 768, "height": 1024})
    guide = page.locator(".arb-bar a.volname")
    assert await guide.is_visible()
    target = await guide.evaluate("link => link.href")
    await guide.tap()
    await page.wait_for_url(target)
    await page.evaluate("window.MathJax?.startup?.promise")
    await page.evaluate("document.fonts.ready")
    contents = page.locator(".ltx_page_main #arb-contents")
    assert await contents.is_visible()
    assert await contents.evaluate("""toc => {
        const top = toc.getBoundingClientRect().top;
        return top >= document.querySelector('.arb-bar').getBoundingClientRect().bottom - 1
            && top < innerHeight;
    }"""), target
    print(f"Navigation passed: {path}")


async def main(base):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path="/usr/bin/chromium")
        page = await browser.new_page(has_touch=True)
        for path in ("crypto-guide/S5.html", "complete/V2.S5.html"):
            await check(page, base.rstrip("/"), path)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))

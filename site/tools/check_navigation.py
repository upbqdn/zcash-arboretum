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


async def check_titles(page, base, path):
    for width in (390, 768, 1440):
        await page.set_viewport_size({"width": width, "height": 1024})
        await ready(page, f"{base}/{path}")
        assert not await page.locator('a a').count(), path
        assert await page.locator('.arb-heading-link').evaluate_all("""links =>
            links.length > 5 && links.every(link => {
                const target = document.getElementById(decodeURIComponent(link.hash.slice(1)));
                return target && link.textContent.trim() &&
                    getComputedStyle(link).color === getComputedStyle(link.parentElement).color;
            })"""), path
        number = page.locator('.ltx_title_section .ltx_tag_section').first
        assert await number.evaluate("node => getComputedStyle(node).position") == (
            'absolute' if width >= 1100 else 'static'), (path, width)
        for kind in ('section', 'subsection', 'paragraph', 'theorem'):
            link = page.locator(f'.ltx_title_{kind} > .arb-heading-link').first
            target = await link.evaluate('link => link.href')
            await link.scroll_into_view_if_needed()
            if width == 1440:
                await link.focus()
                await page.keyboard.press('Enter')
            else:
                await link.tap()
            await page.wait_for_url(target)
            await page.wait_for_function("""() => {
                const node = document.getElementById(decodeURIComponent(location.hash.slice(1)));
                const top = node.getBoundingClientRect().top;
                return top >= document.querySelector('.arb-bar').getBoundingClientRect().bottom - 1
                    && top < innerHeight;
            }""")
        if width == 1440:
            await link.focus()
            assert await link.evaluate("node => getComputedStyle(node).outlineStyle") != 'none'
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        print(f"Title links passed: {path}, {width}px", flush=True)


async def main(base):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path="/usr/bin/chromium")
        page = await browser.new_page(has_touch=True)
        for path in ("crypto-guide/S5.html", "complete/V2.S5.html"):
            await check(page, base.rstrip("/"), path)
        for path in ("crypto-guide/S6.html", "complete/V2.S6.html"):
            await check_titles(page, base.rstrip("/"), path)
        for path in ("math-guide/S10.html", "complete/V1.S10.html"):
            await page.set_viewport_size({"width": 768, "height": 1024})
            await ready(page, f'{base.rstrip("/")}/{path}')
            link = page.locator('.ltx_title_subsection > .arb-heading-link:has(mjx-container)').first
            target = await link.evaluate('link => link.href')
            await link.locator('mjx-container').first.tap()
            await page.wait_for_url(target)
            print(f"Mathematical title link passed: {path}", flush=True)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))

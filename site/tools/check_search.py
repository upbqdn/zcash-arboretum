#!/usr/bin/env python3
"""Search appearance, dismissal and scrolling regression on a served site.

Run: uv run --with playwright python site/tools/check_search.py BASE_URL [ENGINE]
ENGINE defaults to chromium; firefox and webkit require their browser binaries.
Chromium checks native touch input; the other engines check wheel scrolling.
"""

import asyncio
import json
import sys

from playwright.async_api import async_playwright


async def swipe(page, panel):
    box = await panel.bounding_box()
    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] * 0.8
    distance = min(300, box["height"] * 0.6)
    session = await page.context.new_cdp_session(page)
    await session.send("Input.dispatchTouchEvent", {
        "type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    for step in range(1, 11):
        await session.send("Input.dispatchTouchEvent", {
            "type": "touchMove",
            "touchPoints": [{"x": x, "y": y - distance * step / 10}]})
        await page.wait_for_timeout(20)
    await session.send("Input.dispatchTouchEvent", {
        "type": "touchEnd", "touchPoints": []})
    await session.detach()


async def main():
    base = sys.argv[1].rstrip("/")
    engine = sys.argv[2] if len(sys.argv) > 2 else "chromium"
    async with async_playwright() as playwright:
        options = {}
        if engine == "chromium":
            options["executable_path"] = "/usr/bin/chromium"
        browser = await getattr(playwright, engine).launch(**options)
        page = await browser.new_page()
        await page.goto(f"{base}/")
        await page.locator("#search .pagefind-ui__search-input").fill("note")
        await page.locator("#search .pagefind-ui__result").first.wait_for()
        assert await page.locator(".pagefind-ui__result-thumb").count() == 0
        # The landing search is inline, so outside clicks do not dismiss it.
        await page.locator("h1").click()
        assert await page.locator("#search .pagefind-ui__result").first.is_visible()
        await page.close()
        for width, height in ((320, 568), (390, 844), (768, 1024),
                              (1024, 768), (1440, 900), (1920, 1080),
                              (768, 450)):
            page = await browser.new_page(
                viewport={"width": width, "height": height}, has_touch=True)
            await page.goto(f"{base}/wallet-guide/S1.html")
            await page.evaluate("MathJax.startup.promise")
            search = page.locator("details.arb-search")
            summary = search.locator("summary")
            await summary.click()
            field = page.locator("#arb-search-ui .pagefind-ui__search-input")
            await field.fill("note")
            await page.locator("#arb-search-ui .pagefind-ui__result").first.wait_for()
            assert await page.locator(".pagefind-ui__result-thumb").count() == 0
            await field.click()
            assert await search.evaluate("el => el.open")
            await page.locator(".pagefind-ui__result-excerpt").first.click()
            assert await search.evaluate("el => el.open")
            await field.blur()
            panel = page.locator(".arb-search-panel")
            # Ten results overflow even the tallest desktop viewport.
            await page.locator("#arb-search-ui .pagefind-ui__button").last.click()
            await page.wait_for_function(
                "document.querySelectorAll('.pagefind-ui__result').length > 5")
            assert await search.evaluate("el => el.open")
            await panel.evaluate("el => { el.scrollTop = 0; }")
            bounds = await panel.evaluate("""el => ({
                top: el.getBoundingClientRect().top,
                bottom: el.getBoundingClientRect().bottom,
                left: el.getBoundingClientRect().left,
                right: el.getBoundingClientRect().right,
                client: el.clientHeight, scroll: el.scrollHeight,
                overflow: getComputedStyle(el).overflowY,
                viewport: innerHeight
            })""")
            print(json.dumps({"engine": engine, "size": [width, height],
                              **bounds}), flush=True)
            assert 0 <= bounds["top"] < bounds["bottom"] <= height, bounds
            assert 0 <= bounds["left"] < bounds["right"] <= width, bounds
            assert bounds["scroll"] > bounds["client"], bounds
            assert bounds["overflow"] == "auto", bounds
            background = await page.evaluate("scrollY")
            if engine == "chromium":
                await swipe(page, panel)
            else:
                box = await panel.bounding_box()
                await page.mouse.move(box["x"] + box["width"] / 2,
                                      box["y"] + box["height"] / 2)
                await page.mouse.wheel(0, 300)
            await page.wait_for_function(
                "document.querySelector('.arb-search-panel').scrollTop > 0")
            assert await page.evaluate("scrollY") == background
            # The last result and the load-more control must be reachable.
            await panel.evaluate("el => { el.scrollTop = el.scrollHeight; }")
            last = page.locator("#arb-search-ui .pagefind-ui__button").last
            await last.wait_for()
            box = await last.bounding_box()
            assert 0 <= box["y"] < box["y"] + box["height"] <= height
            count = await page.locator("#arb-search-ui .pagefind-ui__result").count()
            await last.click()
            await page.wait_for_function(
                "n => document.querySelectorAll('#arb-search-ui "
                ".pagefind-ui__result').length > n", arg=count)
            assert await search.evaluate("el => el.open")
            # Check gesture containment at the boundary with native touch.
            # Firefox's synthetic wheel also scrolls the document in an
            # isolated overflow: auto / overscroll-behavior: contain fixture;
            # do not mistake that automation path for a real touch test.
            if engine == "chromium":
                await panel.evaluate("el => { el.scrollTop = el.scrollHeight; }")
                before_boundary = await page.evaluate("scrollY")
                await swipe(page, panel)
                assert await page.evaluate("scrollY") == before_boundary
            # Both mouse clicks and touch taps outside dismiss the popup.
            for click in (page.mouse.click, page.touchscreen.tap):
                await click(1, height / 2)
                assert not await search.evaluate("el => el.open")
                await summary.click()
                assert await field.input_value() == "note"
            await field.focus()
            await page.keyboard.press("Escape")
            assert not await search.evaluate("el => el.open")
            assert await summary.evaluate("el => el === document.activeElement")
            await summary.click()
            assert await field.count() == 1  # Reopening reuses the existing UI.
            # Pagefind's own Escape handler clears the query.
            await field.fill("note")
            result = page.locator(".pagefind-ui__result-link").first
            target = await result.evaluate("el => el.href")
            await result.click()
            await page.wait_for_url(target)
            await page.close()
        await browser.close()
    print(f"{engine}: search has no thumbnails; popup scrolls, loads more, "
          "dismisses outside/on Escape, and follows result links.")


if __name__ == "__main__":
    asyncio.run(main())

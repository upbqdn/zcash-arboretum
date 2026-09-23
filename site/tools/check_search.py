#!/usr/bin/env python3
"""Search reading order, appearance, navigation and scrolling regression.

Run: uv run --with playwright python site/tools/check_search.py BASE_URL [ENGINE] [STYLESHEET]
ENGINE defaults to chromium; firefox and webkit require their browser binaries.
Chromium checks native touch input; the other engines check wheel scrolling.
STYLESHEET optionally replaces arboretum.css without changing served HTML/data.
"""

import asyncio
import json
import re
import sys
import unicodedata
from urllib.parse import urlsplit

from playwright.async_api import async_playwright
from sitegen import VOLUMES


async def check_promoted_results(page, base):
    # Compare the native UI with its indexed matches, not a duplicated title
    # heuristic. Intro matches retain their page URL, but use their own excerpt.
    comparisons = await page.locator("#search").evaluate("""async (root, url) => {
        const pagefind = await import(url);
        const {results} = await pagefind.search('note', {sort: {'reading-order': 'asc'}});
        const cards = [...root.querySelectorAll('.pagefind-ui__result')];
        const plain = html => new DOMParser().parseFromString(html, 'text/html')
            .body.textContent.replace(/\\s+/g, ' ').trim();
        return Promise.all(cards.map(async (card, i) => {
            const data = await results[i].data();
            const first = [...data.sub_results].sort(
                (a, b) => a.locations[0] - b.locations[0])[0];
            const title = match => data.meta[`heading-${match.anchor?.id}`] || match.title;
            const link = card.querySelector('.pagefind-ui__result-inner > .pagefind-ui__result-title > a');
            const excerpt = card.querySelector('.pagefind-ui__result-inner > .pagefind-ui__result-excerpt');
            return {href: link.href, expected: new URL(first.anchor ? first.url : data.url, url).href,
                title: link.textContent, expectedTitle: first.anchor ? title(first) : data.meta.title,
                excerpt: plain(excerpt.innerHTML), expectedExcerpt: plain(first.excerpt),
                badge: card.querySelector('[data-pagefind-ui-meta="volume"]')?.textContent.trim(),
                expectedBadge: 'Volume: ' + data.meta.volume, anchored: !!first.anchor,
                internalBadges: [...card.querySelectorAll('[data-pagefind-ui-meta]')]
                    .filter(el => el.dataset.pagefindUiMeta.startsWith('heading-')).length,
                nested: [...card.querySelectorAll('.pagefind-ui__result-nested a')].map(link => {
                    const match = data.sub_results.find(match => new URL(match.url, url).href === link.href);
                    return {href: link.href, title: link.textContent,
                        expectedTitle: match ? title(match) : null};
                })};
        }));
    }""", f"{base}/pagefind/pagefind.js")
    assert any(result["anchored"] for result in comparisons), comparisons
    for result in comparisons:
        assert result["href"] == result["expected"], result
        assert result["title"] == result["expectedTitle"], result
        assert "\x03" not in result["title"], result  # No exposed math placeholder.
        assert result["excerpt"] == result["expectedExcerpt"], result
        assert result["badge"] == result["expectedBadge"], result
        assert result["internalBadges"] == 0, result
        for nested in result["nested"]:
            assert nested["title"] == nested["expectedTitle"], nested
    # Find mathematical headings by their indexed metadata, not stale section IDs
    # or their position on the first page of relevance-ranked results.
    titles = await page.evaluate("""async url => {
        const pagefind = await import(url);
        const titles = async (term, volume) => {
            const {results} = await pagefind.search(term);
            const data = await Promise.all(results.map(result => result.data()));
            return data.filter(result => result.url.includes('/' + volume + '/'))
                .flatMap(result => Object.entries(result.meta)
                    .filter(([key]) => key.startsWith('heading-')).map(([, title]) => title));
        };
        return {seed: await titles('note seed', 'ironwood-guide'),
            field: await titles('group structure', 'math-guide')};
    }""", f"{base}/pagefind/pagefind.js")
    seed_titles = [title for title in titles["seed"] if "The note seed:" in title]
    assert seed_titles, comparisons
    assert all("0x03" in unicodedata.normalize("NFKC", title).replace("\u2062", "")
               for title in seed_titles), seed_titles
    # A real indexed subscript must keep its grouping, not flatten F_p to Fp.
    field_titles = [title for title in titles["field"] if "The group structure of" in title]
    assert field_titles and all(re.search(r"[𝔽F]_\([^)]+\)", title)
                                for title in field_titles), field_titles


async def check_reading_order(page, base):
    expected = await page.evaluate("""async url => {
        const pagefind = await import(url);
        const sorted = await pagefind.search('fiat-', {sort: {'reading-order': 'asc'}});
        const unsorted = await pagefind.search('fiat-');
        const rows = await Promise.all(sorted.results.map(async result => {
            const data = await result.data();
            const matches = [...data.sub_results].sort((a, b) => a.locations[0] - b.locations[0]);
            return {url: new URL(data.url, url).href,
                primary: new URL(matches[0].url, url).href,
                positions: Object.fromEntries(matches.map(match =>
                    [new URL(match.url, url).href, match.locations[0]]))};
        }));
        return {rows, unsorted: await Promise.all(unsorted.results.map(async result =>
            new URL((await result.data()).url, url).href))};
    }""", f"{base}/pagefind/pagefind.js")

    def reading_key(url):
        parts = urlsplit(url).path.split("/")
        volume = next(part for part in parts if part in VOLUMES)
        return VOLUMES.index(volume), tuple(map(int, re.findall(r"\d+", parts[-1])))

    rows = expected["rows"]
    assert len(rows) > 5  # Exercise ordering across the native pagination boundary.
    assert [row["url"] for row in rows] == sorted(expected["unsorted"], key=reading_key)
    previous = None
    for _ in range(2):
        await page.locator("#search input").fill("")
        await page.wait_for_function("!document.querySelector('#search .pagefind-ui__result')")
        await page.locator("#search input").fill("fiat-")
        await page.locator("#search .pagefind-ui__result-link").first.wait_for()
        while True:
            await page.wait_for_function("!document.querySelector('#search .pagefind-ui__loading')")
            cards = await page.locator("#search .pagefind-ui__result").evaluate_all("""cards =>
                cards.map(card => [...card.querySelectorAll('.pagefind-ui__result-link')]
                    .map(link => link.href))""")
            assert 0 < len(cards) <= len(rows), cards
            for links, row in zip(cards, rows):
                assert links[0] == row["primary"], (links, row)
                positions = [row["positions"][link] for link in links]
                assert positions == sorted(positions), (links, positions)
            if len(cards) == len(rows):
                break
            await page.locator("#search .pagefind-ui__button").last.click()
            await page.wait_for_function(
                "n => document.querySelectorAll('#search .pagefind-ui__result').length > n",
                arg=len(cards))
        assert previous is None or cards == previous
        previous = cards


async def check_destination(page, target):
    await page.wait_for_url(target, wait_until="domcontentloaded")
    await page.evaluate("window.MathJax?.startup?.promise")
    await page.evaluate("document.fonts.ready")
    if "#" in target:
        bounds = await page.evaluate("""() => {
            const heading = document.getElementById(decodeURIComponent(location.hash.slice(1)));
            if (!heading) return null;
            const box = heading.getBoundingClientRect();
            return {top: box.top, bottom: box.bottom, viewport: innerHeight,
                bar: document.querySelector('.arb-bar')?.getBoundingClientRect().bottom || 0};
        }""")
        assert bounds, target
        # A near-bottom target may not align to the top, but must remain visible
        # below the sticky bar after MathJax has changed the document's layout.
        assert bounds["bar"] - 1 <= bounds["top"] < bounds["viewport"], (target, bounds)
        assert bounds["bottom"] > bounds["bar"], (target, bounds)


async def check_appearance(page, scope):
    await page.evaluate("document.fonts.ready")
    assert await page.evaluate("""document.fonts.check('16px "EB Garamond"')""")
    for theme in ("light", "warm", "dark", "midnight"):
        await page.evaluate("theme => document.documentElement.dataset.theme = theme",
                            theme)
        appearance = await page.locator(scope).evaluate("""root => {
            const luminance = color => {
                const rgb = color.match(/[\\d.]+/g).slice(0, 3).map(Number)
                    .map(c => c / 255)
                    .map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4);
                return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
            };
            return [...root.querySelectorAll(
                '.pagefind-ui__result-link, .pagefind-ui__result-excerpt')]
                .filter(el => el.getClientRects().length).map(el => {
                const style = getComputedStyle(el);
                let background = el;
                while (getComputedStyle(background).backgroundColor === 'rgba(0, 0, 0, 0)')
                    background = background.parentElement;
                const a = luminance(style.color);
                const b = luminance(getComputedStyle(background).backgroundColor);
                return {font: style.fontFamily, size: parseFloat(style.fontSize),
                    line: parseFloat(style.lineHeight), opacity: style.opacity,
                    contrast: (Math.max(a, b) + .05) / (Math.min(a, b) + .05)};
            });
        }""")
        assert appearance, (scope, theme)
        for style in appearance:
            assert style["font"].split(",")[0].strip('"') == "EB Garamond", (theme, style)
            assert style["size"] >= 14, (theme, style)
            assert style["line"] >= 1.3 * style["size"], (theme, style)
            assert style["opacity"] == "1", (theme, style)
            assert style["contrast"] >= 4.5, (theme, style)
        for element in (page.locator("html"), page.locator(scope)):
            assert await element.evaluate("el => el.scrollWidth <= el.clientWidth + 1"), (
                scope, theme, await element.evaluate("el => [el.scrollWidth, el.clientWidth]"))
    await page.evaluate("delete document.documentElement.dataset.theme")


async def hit_point(page, region, link, padding=False):
    # Click rendered coordinates, not the excerpt element hidden by a stretched
    # anchor. The hit target must be the right native link, including its hash.
    point = await region.evaluate("""(el, padding) => {
        const panel = el.closest('.arb-search-panel');
        if (panel) panel.scrollTop += el.getBoundingClientRect().top -
            panel.getBoundingClientRect().top - 6;
        else el.scrollIntoView({block: 'start'});
        const box = el.getBoundingClientRect();
        return {x: box.left + (padding ? 4 : box.width / 2),
            y: box.top + (padding ? 4 : Math.min(8, box.height / 2))};
    }""", padding)
    target = await link.evaluate("el => el.href")
    hit = await page.evaluate("""({x, y}) =>
        document.elementFromPoint(x, y)?.closest('a')?.href""", point)
    assert hit == target, {"point": point, "hit": hit, "target": target}
    return point, target


async def check_result_links(page, scope, touch=False):
    cards = page.locator(f"{scope} .pagefind-ui__result")
    card = cards.filter(has=page.locator(
        ".pagefind-ui__result-inner > .pagefind-ui__result-excerpt")).first
    nested = page.locator(f'{scope} .pagefind-ui__result-nested:has(a[href*="#"])').first
    await card.wait_for()
    await nested.wait_for()
    assert await nested.evaluate("el => el.getBoundingClientRect().height >= 44")
    main_link = card.locator(
        ".pagefind-ui__result-inner > .pagefind-ui__result-title > a")
    nested_link = nested.locator(".pagefind-ui__result-link")
    assert await nested_link.evaluate("el => !!el.hash")
    assert await nested_link.evaluate("el => el.href") != await nested.locator(
        "xpath=..").locator(":scope > .pagefind-ui__result-title > a").evaluate(
            "el => el.href")
    regions = (
        (card, main_link, True),
        (card.locator(".pagefind-ui__result-inner > .pagefind-ui__result-excerpt"),
         main_link, False),
        (nested, nested_link, True),
        (nested.locator(".pagefind-ui__result-title"), nested_link, False),
    )
    for index, (region, link, padding) in enumerate(regions):
        point, target = await hit_point(page, region, link, padding)
        # Both middle click and Ctrl-click retain native new-tab behaviour.
        control = index == 1
        if control:
            await page.keyboard.down("Control")
        try:
            async with page.context.expect_page() as opened:
                await page.mouse.click(**point, button="left" if control else "middle")
        finally:
            if control:
                await page.keyboard.up("Control")
        popup = await opened.value
        await check_destination(popup, target)
        await popup.close()
    if touch:
        point, target = await hit_point(page, card, main_link, True)
        await page.touchscreen.tap(**point)
    else:
        target = await nested_link.evaluate("el => el.href")
        await nested_link.focus()
        await page.keyboard.press("Shift+Tab")
        await page.keyboard.press("Tab")
        assert await nested_link.evaluate("el => el === document.activeElement")
        assert await nested_link.evaluate("""el => el.matches(':focus-visible') &&
            [getComputedStyle(el), getComputedStyle(el, '::after')].some(style =>
                style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0)""")
        await page.keyboard.press("Enter")
    await check_destination(page, target)


async def check_search_focus(page, base):
    for activation in ("click", "tap", "Enter", "Space"):
        await page.goto(f"{base}/wallet-guide/S1.html")
        await page.evaluate("MathJax.startup.promise")
        search = page.locator("details.arb-search")
        summary = search.locator("summary")
        field = search.locator(".pagefind-ui__search-input")
        for previous, typed in (("", "note"), ("note", "s")):
            await page.evaluate("scrollTo(0, 500)")
            background = await page.evaluate("scrollY")
            if activation == "click":
                await summary.click()
            elif activation == "tap":
                await summary.tap()
            else:
                await summary.focus()
                await page.keyboard.press(activation)
            assert await search.evaluate("el => el.open"), activation
            assert await field.count() == 1
            assert await field.evaluate("el => el === document.activeElement"), activation
            assert await page.evaluate("scrollY") == background, activation
            assert await field.input_value() == previous
            # Real typing must reach the field without clicking or filling it.
            await page.keyboard.type(typed)
            assert await field.input_value() == previous + typed, activation
            await summary.click()
            assert not await search.evaluate("el => el.open"), activation


async def check_same_document(page, base):
    await page.goto(f"{base}/zsa-guide/S5.html")
    await page.evaluate("MathJax.startup.promise")
    search = page.locator("details.arb-search")
    await search.locator("summary").click()
    await page.locator("#arb-search-ui input").fill("note")
    # The first match can be in the introduction, so exercise a nested heading
    # link rather than assuming the main card always has a fragment.
    card = page.locator("#arb-search-ui .pagefind-ui__result-nested").filter(
        has=page.locator("a[href*='zsa-guide/S5.html#']")).first
    await page.locator("#arb-search-ui .pagefind-ui__result-link").first.wait_for()
    while not await card.count():
        await page.wait_for_function("!document.querySelector('#arb-search-ui .pagefind-ui__loading')")
        count = await page.locator("#arb-search-ui .pagefind-ui__result").count()
        await page.locator("#arb-search-ui .pagefind-ui__button").last.click()
        await page.wait_for_function(
            "n => document.querySelectorAll('#arb-search-ui .pagefind-ui__result').length > n",
            arg=count)
    link = card.locator(".pagefind-ui__result-link")
    point, target = await hit_point(page, card, link, True)
    await page.evaluate("window.__arbSameDocumentTest = true")
    await page.mouse.click(**point)
    await check_destination(page, target)
    assert await page.evaluate("window.__arbSameDocumentTest === true")
    assert not await search.evaluate("el => el.open")


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
    stylesheet = sys.argv[3] if len(sys.argv) > 3 else None
    async with async_playwright() as playwright:
        options = {}
        if engine == "chromium":
            options["executable_path"] = "/usr/bin/chromium"
        browser = await getattr(playwright, engine).launch(**options)
        context = await browser.new_context(has_touch=True)
        if stylesheet:
            await context.route("**/arboretum.css*", lambda route: route.fulfill(
                path=stylesheet, content_type="text/css"))
        page = await context.new_page()
        await page.goto(f"{base}/")
        await page.locator("#search .pagefind-ui__search-input").fill("note")
        await page.locator("#search .pagefind-ui__result-link").first.wait_for()
        await page.wait_for_function("!document.querySelector('#search .pagefind-ui__loading')")
        assert await page.locator(".pagefind-ui__result-thumb").count() == 0
        # The landing search is inline, so outside clicks do not dismiss it.
        await page.locator("h1").click()
        assert await page.locator("#search .pagefind-ui__result").first.is_visible()
        await check_promoted_results(page, base)
        await check_appearance(page, "#search")
        await check_reading_order(page, base)
        await check_result_links(page, "#search", touch=True)
        await page.close()
        for width, height in ((320, 568), (390, 844), (768, 1024),
                              (1024, 768), (1440, 900), (1920, 1080),
                              (768, 450)):
            page = await context.new_page()
            await page.set_viewport_size({"width": width, "height": height})
            await page.goto(f"{base}/wallet-guide/S1.html")
            await page.evaluate("MathJax.startup.promise")
            search = page.locator("details.arb-search")
            summary = search.locator("summary")
            await summary.click()
            field = page.locator("#arb-search-ui .pagefind-ui__search-input")
            await field.fill("note")
            await page.locator("#arb-search-ui .pagefind-ui__result-link").first.wait_for()
            await page.wait_for_function(
                "!document.querySelector('#arb-search-ui .pagefind-ui__loading')")
            assert await page.locator(".pagefind-ui__result-thumb").count() == 0
            await field.click()
            assert await search.evaluate("el => el.open")
            await check_appearance(page, "#arb-search-ui")
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
                clientWidth: el.clientWidth, scrollWidth: el.scrollWidth,
                overflow: getComputedStyle(el).overflowY,
                viewport: innerHeight
            })""")
            print(json.dumps({"engine": engine, "size": [width, height],
                              **bounds}), flush=True)
            assert 0 <= bounds["top"] < bounds["bottom"] <= height, bounds
            assert 0 <= bounds["left"] < bounds["right"] <= width, bounds
            assert bounds["scroll"] > bounds["client"], bounds
            assert bounds["scrollWidth"] <= bounds["clientWidth"] + 1, bounds
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
                assert await field.evaluate("el => el === document.activeElement")
                field_box = await field.bounding_box()
                panel_box = await panel.bounding_box()
                assert panel_box["y"] <= field_box["y"]
                assert field_box["y"] + field_box["height"] <= panel_box["y"] + panel_box["height"]
            await field.focus()
            await page.keyboard.press("Escape")
            assert not await search.evaluate("el => el.open")
            assert await summary.evaluate("el => el === document.activeElement")
            await summary.click()
            assert await field.count() == 1  # Reopening reuses the existing UI.
            # Pagefind's own Escape handler clears the query.
            await field.fill("note")
            await check_result_links(page, "#arb-search-ui")
            if (width, height) == (768, 1024):
                guide = page.locator(".arb-bar a.volname")
                assert await guide.get_attribute("title") == "Table of contents"
                target = await guide.evaluate("el => el.href")
                await guide.tap()
                await page.wait_for_url(target)
                assert await page.locator(".ltx_page_main .ltx_TOC").is_visible()
            await page.close()
        page = await context.new_page()
        await check_search_focus(page, base)
        await check_same_document(page, base)
        await browser.close()
    print(f"{engine}: search is legible in every theme without horizontal overflow; "
          "reading order, pagination, repeat queries and guide-title TOC links pass; "
          "parent/nested cards follow native links from padding, excerpts and titles; "
          "touch, keyboard, Ctrl/middle-click, scrolling, load-more, dismissal "
          "and no thumbnails pass.")


if __name__ == "__main__":
    asyncio.run(main())

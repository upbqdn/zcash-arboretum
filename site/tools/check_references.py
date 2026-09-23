#!/usr/bin/env python3
"""Exercise native cross-guide links, including typeset math and named results.

Run: uv run --with playwright python site/tools/check_references.py BASE_URL
"""

import asyncio
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from playwright.async_api import async_playwright

from check_navigation import ready
from check_search import check_destination
from sitegen import VOLUMES


# Source pages are fixtures; destinations come from the rendered citations.
CASES = (
    ("ironwood-guide", "S2.html", "The random oracle model", "crypto-guide", 390, "tap"),
    ("ironwood-guide", "S11.html", "invariant and the GLV endomorphism", "math-guide", 768, "math"),
    ("ironwood-guide", "S11.html", "From statement to circuit", "halo2-guide", 1440, "keyboard"),
    ("ironwood-guide", "S11.html", "The lookup argument", "halo2-guide", 1440, "click"),
    ("ironwood-guide", "S11.html", "Accumulation and the Halo", "halo2-guide", 768, "tap"),
    ("ironwood-guide", "S8.html", "Commitment schemes", "crypto-guide", 1440, "click"),
    ("zsa-guide", "S2.html", "The general form: triples", "wallet-guide", 390, "tap"),
    ("zsa-guide", "S4.html", "Orchard Action", "ironwood-guide", 768, "keyboard"),
    ("zsa-guide", "S2.html", "Net value commitment", "ironwood-guide", 1440, "click"),
    ("ironwood-guide", "S1.html", "Math Guide", "math-guide", 390, "tap"),
)


async def main(base):
    base = base.rstrip("/")
    output = Path(__file__).resolve().parents[2] / "build/refs-check"
    output.mkdir(parents=True, exist_ok=True)
    errors = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path="/usr/bin/chromium")
        page = await browser.new_page(has_touch=True)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("response", lambda response: errors.append(
            f"HTTP {response.status}: {response.url}") if response.status >= 400 else None)
        for complete in (False, True):
            edition = "complete" if complete else "standalone"
            for source, filename, phrase, guide, width, action in CASES:
                await page.set_viewport_size({"width": width, "height": 1000})
                path = (f"complete/V{VOLUMES.index(source) + 1}.{filename}"
                        if complete else f"{source}/{filename}")
                await ready(page, f"{base}/{path}")
                assert not await page.locator("a a, mjx-merror, merror").count(), path
                link = page.locator("a.arb-crossref").filter(
                    has_text=re.compile(r"\s+".join(map(re.escape, phrase.split())))).first
                target = await link.evaluate("link => link.href")
                destination = urlsplit(target)
                number = VOLUMES.index(guide) + 1
                guide_only = phrase.endswith("Guide")
                suffix = (f"/complete/Pt{number}.html" if complete
                          else f"/{guide}/") if guide_only else (
                              f"/complete/V{number}.S" if complete else f"/{guide}/S")
                assert suffix in destination.path, (path, phrase, target)
                assert not guide_only or not destination.fragment, target
                if action == "math":
                    math = link.locator("mjx-container").first
                    assert await math.count(), await link.inner_html()
                    await link.scroll_into_view_if_needed()
                    await page.screenshot(path=str(output / f"{edition}-math-citation-768.png"))
                    await math.click()
                elif action == "keyboard":
                    await link.focus()
                    await page.keyboard.press("Enter")
                elif action == "tap":
                    await link.tap()
                else:
                    await link.click()
                await check_destination(page, target)
                assert not await page.locator("a a, mjx-merror, merror").count(), target
                heading = await page.evaluate("""() => {
                    const target = location.hash
                        ? document.getElementById(decodeURIComponent(location.hash.slice(1)))
                        : document.querySelector('.ltx_page_main h1');
                    return (target.querySelector('.ltx_title') || target).textContent;
                }""")
                assert re.search(r"\s+".join(map(re.escape, phrase.split())), heading), (target, heading)
                assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), target
                if action == "math":
                    await page.screenshot(path=str(output / f"{edition}-math-target-768.png"))
                print(f"{edition} {width}px {action}: {phrase} → {target}", flush=True)
            # LaTeXML has already resolved these references; MathJax must
            # retain their numbers and links, not replace them with ???.
            path = 'complete/V5.S2.html' if complete else 'ironwood-guide/S2.html'
            table_id = '#Ex639' if complete else '#Ex1'
            prefix = 'V5.' if complete else ''
            expected = [(prefix + name, label) for name, label in (
                ('S3.html', '3'), ('S7.html', '7'), ('S3.html', '3'),
                ('S4.html', '4'), ('S3.html', '3'), ('S6.html', '6'),
                ('S7.html', '7'))] + [('#SS3', '2.3')]
            for width in (390, 768, 1440):
                await page.set_viewport_size({'width': width, 'height': 1000})
                for index in (0, 7):
                    await ready(page, f'{base}/{path}')
                    table = page.locator(table_id)
                    # MathJax's accessible explorer owns links inside math.
                    links = table.locator('mjx-container a[data-mjx-href]')
                    actual = await links.evaluate_all(
                        'links => links.map(a => [a.dataset.mjxHref, a.textContent])')
                    assert actual == [list(item) for item in expected], (path, actual)
                    assert '???' not in await table.inner_text(), path
                    assert not await page.locator('mjx-merror, merror').count(), path
                    if width == 768 and index == 0:
                        await table.scroll_into_view_if_needed()
                        await page.screenshot(path=str(output / f'{edition}-domain-separators-768.png'))
                    target = await links.nth(index).evaluate(
                        'a => new URL(a.dataset.mjxHref, location.href).href')
                    if width == 1440:
                        await table.locator('mjx-container').focus()
                        await page.keyboard.press('Enter')
                        for _ in range(index + 1):
                            await page.keyboard.press('Tab')
                        await page.keyboard.press('Enter')
                    else:
                        await links.nth(index).tap()
                    await check_destination(page, target)
                print(f'{edition} {width}px: domain-separator references passed', flush=True)
        assert not errors, errors
        await browser.close()
    print("Cross-guide links passed in both editions at phone, tablet and desktop widths.")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))

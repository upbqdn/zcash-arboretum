#!/usr/bin/env python3
"""Check pre-rendered figures are not clipped by LaTeXML resizebox wrappers.

Run: uv run --with playwright python site/tools/check_figures.py BASE_URL
Add --candidate to test local CSS, fonts and figures against published HTML.
"""

import asyncio
import mimetypes
from pathlib import Path
import sys
from urllib.parse import urlsplit

from playwright.async_api import async_playwright

from check_navigation import ready

ROOT = Path(__file__).resolve().parents[2]


async def main(base, candidate=False):
    base = base.rstrip("/")
    output = ROOT / "build" / "figure-check"
    output.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path="/usr/bin/chromium")
        page = await browser.new_page()
        if candidate:
            async def local_asset(route):
                path = urlsplit(route.request.url).path
                if path.endswith("/arboretum.css"):
                    file = ROOT / "site/arboretum.css"
                elif "/fonts/" in path:
                    file = ROOT / "site/fonts" / path.rsplit("/", 1)[-1]
                elif "/figures/" in path:
                    file = ROOT / "site/figures" / path.rsplit("/", 1)[-1]
                else:
                    await route.continue_()
                    return
                await route.fulfill(path=str(file), content_type=mimetypes.guess_type(file)[0])
            await page.route(f"{base}/**", local_asset)

        for volume in ("ironwood-guide", "complete"):
            for section, number in ((3, 2), (7, 4), (8, 5)):
                prefix = "V5." if volume == "complete" else ""
                path = f"{volume}/{prefix}S{section}.html"
                await ready(page, f"{base}/{path}")
                img = page.locator(f'img[src*="ironwood-guide-fig{number}.png"]')
                await img.evaluate("image => image.decode()")
                for width in (320, 390, 768, 1024, 1440):
                    await page.set_viewport_size({"width": width, "height": 1000})
                    await page.evaluate("new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                    report = await img.evaluate("""image => {
                      const figure = image.closest('figure');
                      const picture = image.getBoundingClientRect();
                      const box = figure.getBoundingClientRect();
                      const caption = figure.querySelector('figcaption').getBoundingClientRect();
                      return {width: box.width, top: picture.top - box.top, left: picture.left - box.left,
                        right: box.right - picture.right, bottom: caption.top - picture.bottom,
                        ratio: picture.width / picture.height,
                        naturalRatio: image.naturalWidth / image.naturalHeight};
                    }""")
                    assert all(report[edge] >= -1 for edge in ("top", "left", "right", "bottom")), (path, width, report)
                    assert abs(report["ratio"] - report["naturalRatio"]) < .01, (path, width, report)
                    assert report["width"] <= width + 1, (path, width, report)
                    await img.screenshot(path=str(output / f"{volume}-fig{number}-{width}.png"))
                    print(path, width, report, flush=True)

        # A non-image transformed box must retain its authored transform/height.
        assert await page.evaluate("""() => {
          const figure = document.createElement('figure');
          figure.className = 'ltx_figure';
          figure.innerHTML = '<div class="ltx_transformed_outer" style="height:15px">' +
            '<span class="ltx_transformed_inner" style="transform:scale(2)"><math><mi>x</mi></math></span></div>';
          document.body.append(figure);
          const unchanged = getComputedStyle(figure.firstElementChild).height === '15px' &&
            getComputedStyle(figure.querySelector('span')).transform !== 'none';
          figure.remove();
          return unchanged;
        }""")
        await browser.close()
    print("All three transformed diagrams passed at five widths in both editions.")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], "--candidate" in sys.argv))

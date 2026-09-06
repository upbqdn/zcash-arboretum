#!/usr/bin/env python3
"""Check generated HTML for duplicate IDs and broken local links/assets."""

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.duplicates = set()
        self.links = []
        self.errors = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img" and not attrs.get("src"):
            self.errors.append("image has no source")
        if "ltx_ERROR" in attrs.get("class", "").split():
            self.errors.append("LaTeXML error markup")
        if identifier := attrs.get("id"):
            if identifier in self.ids:
                self.duplicates.add(identifier)
            self.ids.add(identifier)
        for attr in ("href", "src"):
            if value := attrs.get(attr):
                self.links.append(value)


def check(out):
    out = Path(out).resolve()
    pages = {path: Page(path.read_text()) for path in out.rglob("*.html")}
    errors = []
    if not pages:
        errors.append("no HTML pages")
    for path, page in pages.items():
        errors.extend(f"{path.relative_to(out)}: {error}" for error in page.errors)
        for identifier in sorted(page.duplicates):
            errors.append(f"{path.relative_to(out)}: duplicate ID {identifier}")
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            target = ((out / unquote(url.path).lstrip("/"))
                      if url.path.startswith("/") else
                      (path.parent / unquote(url.path)) if url.path else path)
            target = target.resolve()
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{path.relative_to(out)}: missing {link}")
            elif url.fragment and target in pages:
                if unquote(url.fragment) not in pages[target].ids:
                    errors.append(f"{path.relative_to(out)}: missing anchor {link}")
    return len(pages), errors


if __name__ == "__main__":
    count, errors = check(sys.argv[1])
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Site link/ID gate passed: {count} HTML pages")

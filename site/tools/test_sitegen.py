#!/usr/bin/env python3
"""Small regression check for shared generated-site controls."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import sitegen  # noqa: E402
from check_build import log_errors, source_errors  # noqa: E402
from check_site import check  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    assert check(out)[1] == ["no HTML pages"]
    (out / "index.html").write_text('<a href="other/?v=1#ok">next</a>')
    (out / "other").mkdir()
    (out / "other" / "index.html").write_text('<p id="ok">OK</p>')
    assert check(out) == (2, [])
    (out / "other" / "index.html").write_text(
        '<p id="wrong"></p><p id="wrong"></p><img src="missing.png">')
    errors = check(out)[1]
    assert len(errors) == 3, errors
    assert any("missing anchor" in error for error in errors)
    assert any("duplicate ID" in error for error in errors)
    assert any("missing missing.png" in error for error in errors)
    (out / "other" / "index.html").write_text(
        '<p id="ok"></p><img src=""><span class="ltx_ERROR">bad</span>')
    errors = check(out)[1]
    assert len(errors) == 2, errors
    assert any("image has no source" in error for error in errors)
    assert any("LaTeXML error markup" in error for error in errors)

assert not log_errors("Underfull \\hbox (badness 1000)\nOutput written.")
document = "\\begin{document}\nText.\n\\end{document}\n"
assert not source_errors(document + "% A trailing comment is fine.\n")
assert source_errors(document + "discarded text")
assert source_errors(document + document)
assert source_errors("")
for warning in (r"Overfull \hbox (2.0pt too wide)",
                r"Overfull \vbox (2.0pt too high)",
                "LaTeX Warning: There were undefined references.",
                "LaTeX Warning: Label `sec:x' multiply defined.",
                "Missing character: There is no x in font nullfont!",
                "! Undefined control sequence."):
    assert log_errors(warning), warning

PARKED = ("pq-guide", "tachyon-guide", "voting-guide")
MERGED = "halo2-intuition-guide"
assert set(PARKED).isdisjoint(sitegen.VOLUMES)
assert MERGED not in sitegen.VOLUMES
assert not (sitegen.ROOT / f"{MERGED}.tex").exists()
assert not (sitegen.ROOT / f"{MERGED}.pdf").exists()
assert next((group, chip) for vol, group, chip in sitegen.VOLUME_META
            if vol == "flyclient-guide") == ("Frontier", "design-stage")


with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    sitegen.landing(out)
    sitegen.concordance(out)
    for name in ("index.html", "concordance.html"):
        html = (out / name).read_text()
        assert html.index(sitegen.THEME_INIT) < html.index("arboretum.css")
        assert html.count('class="arb-theme"') == 1
        for value in ("system", "light", "warm", "dark", "midnight"):
            assert f'value="{value}"' in html
        assert ">Warm light</option>" in html
        assert ">Warm dark</option>" in html

    landing = (out / "index.html").read_text()
    concordance = (out / "concordance.html").read_text()
    assert "ZIP 316" in concordance
    assert "<table></table>" not in concordance
    assert "<h2>Protocol specification</h2>" not in concordance
    for vol in PARKED:
        assert f'href="{vol}/"' not in landing
        assert f'href="{vol}/"' not in concordance
    assert f'href="{MERGED}/"' not in landing
    assert f'href="{MERGED}/"' not in concordance
    assert landing.count('href="complete/"') == 2
    assert landing.count('href="pdf/arboretum-complete.pdf"') == 1
    assert "Foundations, core protocol, and frontier designs" in landing
    assert landing.index('<h3 class="grp">Frontier</h3>') < landing.index(
        '<h3 class="grp">Complete edition</h3>')
    assert (out / "pdf" / "arboretum-complete.pdf").is_file()

    omnibus = out / "arboretum-complete.tex"
    sitegen.omnibus(out=omnibus)
    complete_tex = omnibus.read_text()
    native_section_id = (
        r"\def\thesection@ID{V\arabic{arbvolume}.S\@section@ID}")
    assert native_section_id not in complete_tex
    assert sitegen.OMNIBUS_INTRO in complete_tex
    assert r"\setlength{\headheight}{20pt}" in complete_tex
    assert complete_tex.count("\\stepcounter{arbvolume}") == len(
        sitegen.VOLUMES)
    assert "\\part*{How Halo 2 Proves:" not in complete_tex
    assert "\\section{From a relation to a circuit}" in complete_tex
    for title in ("PQ Guide", "Tachyon Guide", "Voting Guide"):
        assert f"\\part{{{title}:" not in complete_tex

    webdir = out / "web"
    webdir.mkdir()
    with patch.object(sitegen, "WEBDIR", webdir):
        sitegen.webprep()
    for volume in ("math-guide", "crypto-guide", "arboretum-complete"):
        assert r"\mdfsetup" not in (webdir / f"{volume}.tex").read_text()
    assert "Statistical distance" in (webdir / "math-guide.tex").read_text()
    assert "FF1" in (webdir / "crypto-guide.tex").read_text()
    (webdir / "math-guide.tex").write_text(r"""\documentclass{article}
\begin{document}
\begin{abstract}
Volume summary.
\end{abstract}
\section{First section}
\end{document}
""")
    web_omnibus = out / "web-complete.tex"
    with patch.object(sitegen, "WEBDIR", webdir):
        sitegen.omnibus(webdir, web_omnibus)
    web_tex = web_omnibus.read_text()
    assert web_tex.count(native_section_id) == 1
    assert web_tex.index(native_section_id) < web_tex.index(r"\begin{document}")
    assert "\\begin{abstract}" not in web_tex
    assert web_tex.index("Volume summary.") < web_tex.index(
        "\\section{First section}")

    page = out / "math-guide" / "index.html"
    page.parent.mkdir()
    page.write_text(
        '<html><head><link rel="stylesheet" '
        'href="_site/math-guide/arboretum.css"></head>'
        '<body><main class="ltx_page_content">'
        '<div id="Thmtheorem1" class="ltx_theorem ltx_theorem_proposition">'
        '<h6 class="ltx_title ltx_runin ltx_title_theorem">'
        '<span class="ltx_tag ltx_tag_theorem">Proposition 1.1</span> '
        '(<a class="ltx_ref" href="#Thmtheorem0">prior result</a>).'
        '</h6><div class="ltx_para"><p>A result.</p></div></div>'
        '<div class="ltx_proof"><p>'
        'Given <math display="inline" alttext="S"><mi>S</mi></math>, thus '
        '<math display="inline" alttext="x=1"><mi>x</mi></math>.\n∎'
        '</p><p>Done.\n∎</p></div></main>'
        '<footer><div>Generated on today by '
        '<a class="ltx_LaTeXML_logo">LaTeXML</a></div></footer></body></html>')
    complete_page = out / "complete" / "index.html"
    complete_page.parent.mkdir()  # A failed prior build may leave the directory.
    run = sitegen.subprocess.run

    def build_complete(args, **kwargs):
        if args[0] != "latexmlc":
            return run(args, **kwargs)
        assert args[-1] == "build/web/arboretum-complete.tex"
        assert kwargs == {"cwd": sitegen.ROOT, "check": True}
        complete_page.write_text(
            '<html><head><link rel="stylesheet" href="../arboretum.css"></head>'
            '<body><main class="ltx_page_content"></main>'
            '<footer><div></div></footer></body></html>')

    with patch.object(sitegen.subprocess, "run", side_effect=build_complete):
        sitegen.postprocess(out)
    html = page.read_text()
    assert html.index(sitegen.THEME_INIT) < html.index("arboretum.css")
    assert html.count('class="arb-theme"') == 1
    assert '<body data-arb="vol">' in html
    assert html.count("window.MathJax") == 1
    assert 'href="../arboretum.css?v=' in html
    assert 'href="_site/math-guide/arboretum.css"' not in html
    assert 'font: \'mathjax-stix2\'' in html
    assert "macros: { qed: '\\\\tag*{□}' }" in html
    assert "linebreaks: { inline: true" in html
    assert "replace(/%\\s+/g, '')" in html
    assert 'src="../mathjax/tex-chtml.js"' in html
    assert ('<a class="ltx_ref" href="#Thmtheorem0">prior result</a>).'
            '<a class="arb-permalink" href="#Thmtheorem1" '
            'aria-label="Permalink to this item" '
            'title="Permalink">#</a></h6>') in html
    assert html.count('class="arb-permalink"') == 1
    assert ('<span class="arb-proof-end"><math display="inline" '
            'alttext="x=1"><mi>x</mi></math>.</span> '
            '<span class="arb-qed">□</span>') in html
    assert html.count('class="arb-proof-end"') == 1
    assert html.count('class="arb-qed"') == 2
    complete_html = complete_page.read_text()
    assert '<body data-pagefind-ignore data-arb="vol">' in complete_html
    assert '../pdf/arboretum-complete.pdf' in complete_html
    assert 'The Complete Arboretum' in complete_html
    assert (out / "mathjax" / "tex-chtml.js").is_file()
    boldsymbol = out / "mathjax" / "input" / "tex" / "extensions" / "boldsymbol.js"
    assert 'checkVersion("[tex]/boldsymbol","4.1.1"' in boldsymbol.read_text()
    assert (out / "@mathjax" / "mathjax-stix2-font" / "chtml.js").is_file()

    # A second finishing pass must not duplicate controls, scripts or IDs.
    sitegen.postprocess(out)
    assert page.read_text() == html
    assert complete_page.read_text() == complete_html

    page.write_text(page.read_text().replace(
        "Done.", r"Done \crefpairconjunction."))
    try:
        sitegen.postprocess(out)
    except RuntimeError as error:
        assert r"\crefpairconjunction" in str(error)
    else:
        raise AssertionError("unexpanded cross-reference macro was accepted")

css = (sitegen.ROOT / "site" / "arboretum.css").read_text()
assert ':root[data-theme="warm"]' in css
assert ':root[data-theme="dark"]' in css
assert ':root[data-theme="midnight"]' in css
assert '.ltx_theorem .arb-permalink {' in css
assert 'a[rel="next"] { margin-left: 0; align-self: flex-end; }' in css
assert 'mjx-container.arb-math-scroll' in css
search_panel = css.split('.arb-bar .arb-search-panel {', 1)[1].split('}', 1)[0]
assert 'max-height: calc(100dvh - 4rem)' in search_panel
assert 'overflow-y: auto' in search_panel
assert 'overscroll-behavior-y: contain' in search_panel
assert (sitegen.ROOT / "site" / "mathjax" / "tex-chtml.js").is_file()
assert (sitegen.ROOT / "site" / "@mathjax" / "mathjax-stix2-font"
        / "chtml.js").is_file()
print("site generator checks passed")

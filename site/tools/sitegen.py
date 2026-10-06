#!/usr/bin/env python3
"""Site tooling for the Zcash Arboretum.

Modes:
  volumes  Print the volumes included in the Arboretum.
  render   Pre-render every tikzpicture to SVG and PNG (needs tectonic,
           pdftocairo, and pdftoppm; run locally, commit both formats).
  webprep  Write build/web/<vol>.tex with tikzpictures replaced by
           \\includegraphics of the pre-rendered PNGs and tikz packages
           stripped (run in CI before latexml).
  landing  Write the landing page index.html from the volumes' \\title
           lines into the directory given by --out.
  concordance  Index ZIP and protocol-section citations into --out.
  omnibus  Generate the complete edition's LaTeX source.
  postprocess  Finish the generated HTML pages in --out.
"""

import datetime
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from html import escape, unescape
from html.parser import HTMLParser
from itertools import takewhile
from pathlib import Path

from mathbreak import SCRIPTED, pieces

ROOT = Path(__file__).resolve().parents[2]
FIGDIR = ROOT / "site" / "figures"
WEBDIR = ROOT / "build" / "web"

# Reading order and grouping for the landing page.
VOLUME_META = [
    ("math-guide", "Foundations"),
    ("crypto-guide", "Foundations"),
    ("halo2-guide", "Foundations"),
    ("consensus-guide", "Deployed protocol"),
    ("ironwood-guide", "Deployed protocol"),
    ("wallet-guide", "Deployed protocol"),
    ("flyclient-guide", "Frontier"),
    ("zsa-guide", "Frontier"),
    ("frost-guide", "Frontier"),
]
VOLUMES = [v for v, _ in VOLUME_META]
# What each group covers and rests on, under its heading on the landing.
GROUP_GLOSS = {
    "Foundations": "The mathematics, cryptography, and proof system, from first principles",
    "Deployed protocol": "Consensus, the shielded payment, and the wallet, built on the foundations",
    "Frontier": "Light clients, shielded assets, and threshold signing, on the deployed protocol",
}

OMNIBUS_INTRO = r"""\phantomsection
\section*{Introduction}
\addcontentsline{toc}{section}{Introduction}
\markboth{Introduction}{}
\emph{The Zcash Arboretum} is a non-normative guide to the mathematics,
cryptography, and engineering of the Zcash protocol.  It covers the
foundations of Halo~2 and Orchard, deployed consensus and wallet protocols,
and designs being explored beyond them.  The protocol specification,
applicable ZIPs, and consensus rules remain authoritative.

The order is layered.  The \emph{Math}, \emph{Crypto}, and \emph{Halo~2}
Guides construct the foundations.  The \emph{Consensus}, \emph{Ironwood},
and \emph{Wallet} Guides explain the deployed system and its
boundaries.  The remaining parts examine the unbuilt FlyClient bridge,
shielded assets, and threshold authorization.

Three reading paths cover most uses.  For prerequisites, begin with the first
three parts; readers new to proof systems may start with the worked example
that closes the Halo~2 Guide.  For the life of a shielded payment, read
\emph{Ironwood}, then \emph{Wallet} and \emph{Consensus}.  For
proposed changes, read the relevant frontier part only after its lower-layer
dependencies.  Each part restarts its own section numbering so that citations
agree with the separately published volume.
"""

# Two themes; the retired warm and midnight keys map to them.
THEME_INIT = """<script>
try {
  const theme = {light: 'light', warm: 'light', dark: 'dark', midnight: 'dark'}[
    localStorage.getItem('arb-theme')];
  if (theme) document.documentElement.dataset.theme = theme;
} catch (_) {}
</script>"""
# The current choice's icon in the phone bar: a sun, a half-filled circle (System), a moon.
THEME_ICONS = ''.join(
    f'<svg class="arb-mark-{k}" viewBox="0 0 24 24">{body}</svg>' for k, body in (
        ("light", '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4'
                  'M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/>'),
        ("system", '<circle cx="12" cy="12" r="8.5"/>'
                   '<path class="arb-fill" d="M12 3.5a8.5 8.5 0 0 1 0 17z"/>'),
        ("dark", '<path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a6.6 6.6 0 0 0 11 11z"/>')))
# "Theme" (in the phone bar, the icon) opens Light, System and Dark beneath it, as Search
# opens its panel. System clears the stored key.
THEME_MENU = ('<details class="arb-theme"><summary aria-label="Theme">'
              '<span class="arb-theme-word">Theme</span>'
              '<span class="arb-theme-mark" aria-hidden="true">' + THEME_ICONS + '</span></summary>'
              '<span class="arb-themes" role="radiogroup" aria-label="Theme">'
              '<label><input type="radio" name="arb-theme" value="light">Light</label>'
              '<label><input type="radio" name="arb-theme" value="system">System</label>'
              '<label><input type="radio" name="arb-theme" value="dark">Dark</label></span></details>')
# The theme control, the fitting of wide displays, the scroll-edge fades and the Contents
# disclosure.
PAGE_SCRIPT = """<script>
(function () {
  const root = document.documentElement;
  const menu = document.querySelector('details.arb-theme');
  const radios = document.querySelectorAll('.arb-themes input');
  function show() {
    const theme = root.dataset.theme || 'system';
    radios.forEach(function (r) { r.checked = r.value === theme; });
    if (!menu) return;
    const name = 'Theme: ' + theme[0].toUpperCase() + theme.slice(1);
    menu.querySelector('summary').title = name;
    menu.querySelector('summary').setAttribute('aria-label', name);
  }
  radios.forEach(function (r) {
    r.addEventListener('change', function () {
      try {
        if (r.value === 'system') {
          delete root.dataset.theme;
          localStorage.removeItem('arb-theme');
        } else {
          root.dataset.theme = r.value;
          localStorage.setItem('arb-theme', r.value);
        }
      } catch (_) {}
      show();
    });
  });
  show();
  // The panel closes on a choice (a click, or Enter, which Firefox would let reopen it), Escape,
  // a click outside, or focus leaving it.
  if (menu) {
    const close = function () {
      if (menu.contains(document.activeElement)) menu.querySelector('summary').focus();
      menu.open = false;
    };
    menu.addEventListener('click', function (e) { if (e.target.localName === 'label') close(); });
    menu.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && e.target.type === 'radio') { e.preventDefault(); close(); }
    });
    menu.addEventListener('focusout', function (e) {
      if (e.relatedTarget && !menu.contains(e.relatedTarget)) menu.open = false;
    });
    document.addEventListener('click', function (e) {
      if (menu.open && !menu.contains(e.target)) menu.open = false;
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menu.open) close();
    });
  }
  // A display, table or verbatim box that scrolls fades the edge where content is hidden.
  const boxes = '.ltx_eqn_table, .ltx_page_main :is(table.ltx_tabular, pre), .arb-math-scroll';
  function edge(b) {
    const more = b.scrollWidth - b.clientWidth;
    b.classList.toggle('arb-more-l', more > 1 && b.scrollLeft > 1);
    b.classList.toggle('arb-more-r', more > 1 && b.scrollLeft < more - 1);
  }
  function edges() { document.querySelectorAll(boxes).forEach(edge); }
  document.addEventListener('scroll', function (e) {
    if (e.target.matches && e.target.matches(boxes)) edge(e.target);
  }, true);
  // On wider screens a display or table wider than the column shrinks to fit, to 75 % at most;
  // beyond that it scrolls. The fixed widths of a table's paragraph columns shrink with it.
  const roomy = matchMedia('(min-width: 701px)');
  function shrink() {
    document.querySelectorAll('.ltx_eqn_table, .ltx_page_main table.ltx_tabular').forEach(function (t) {
      const fixed = t.querySelectorAll('[style*="width:"]');
      t.style.fontSize = '';
      fixed.forEach(function (e) { if (e.dataset.w) e.style.width = e.dataset.w; });
      if (!roomy.matches) return;
      // a formula's spacing does not scale exactly, so a step or two more
      const base = parseFloat(getComputedStyle(t).fontSize);
      for (let k = 1, i = 0; i < 4 && k > .75 && t.scrollWidth > t.clientWidth + 1; i++) {
        k = Math.max(.75, .995 * k * t.clientWidth / t.scrollWidth);
        t.style.fontSize = k * base + 'px';
        fixed.forEach(function (e) {
          e.dataset.w = e.dataset.w || e.style.width;
          e.style.width = 'calc(' + e.dataset.w + ' * ' + k + ')';
        });
      }
    });
  }
  // after the formula script's boxes too
  const refresh = () => requestAnimationFrame(function () { shrink(); edges(); });
  document.fonts.ready.then(refresh);
  let timer;
  addEventListener('resize', function () { clearTimeout(timer); timer = setTimeout(refresh, 400); });
  const toc = document.querySelector('details.arb-toc');
  const nav = document.querySelector('.ltx_page_navbar');
  if (!toc || !nav) return;
  document.addEventListener('click', function (e) {
    if (!toc.open) return;
    if (e.target.closest('.ltx_page_navbar a')) toc.open = false;
    else if (!toc.contains(e.target) && !nav.contains(e.target)) toc.open = false;
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && toc.open) { toc.open = false; toc.querySelector('summary').focus(); }
  });
})();
</script>"""

# Pagefind prints tags as bare "Key: value" text; the volume's key becomes the tag's
# data-pagefind-ui-meta attribute, which the stylesheet prints alone ("V Ironwood Guide").
SEARCH_OPTIONS = """showSubResults: true, showImages: false, excerptLength: 20,
    sort: { 'reading-order': 'asc' },
    processResult: function (result) {
      const meta = { ...result.meta };
      const matches = (result.sub_results || []).map(match => ({
        ...match,
        title: meta[`heading-${match.anchor?.id}`] || match.title
      })).sort((a, b) => a.locations[0] - b.locations[0]);
      if (meta.volume) { meta[meta.volume] = ''; delete meta.volume; }
      for (const key of Object.keys(meta))
        if (key.startsWith('heading-')) delete meta[key];
      result = { ...result, meta, sub_results: matches };
      const first = matches[0];
      if (first) {
        if (first.anchor)
          result.meta = { ...result.meta, title: first.title, url: first.url };
        result.excerpt = first.excerpt;
      }
      return result;
    }"""

TOC_SCRIPT = """<script>
(function () {
  const sidebar = document.querySelector('.ltx_page_navbar');
  if (!sidebar) return;
  const entries = [...sidebar.querySelectorAll('a[href^="#"]')]
    .map(link => [link, document.getElementById(decodeURIComponent(link.hash.slice(1)))])
    .filter(([, section]) => section);
  if (!entries.length) return;
  const bar = document.querySelector('.arb-bar');
  let current, frame;
  function update() {
    frame = 0;
    if (!sidebar.getClientRects().length) return;
    const top = Math.max(bar?.getBoundingClientRect().bottom || 0,
      parseFloat(getComputedStyle(entries[0][1]).scrollMarginTop) || 0) + 1;
    let active;
    for (const [link, section] of entries)
      if (section.getBoundingClientRect().top <= top) active = link;
    if (scrollY > 0 && scrollY + innerHeight >= document.documentElement.scrollHeight - 2)
      active = entries.at(-1)[0];
    if (active === current) return;
    current?.removeAttribute('aria-current');
    active?.setAttribute('aria-current', 'location');
    current = active;
  }
  function schedule() { if (!frame) frame = requestAnimationFrame(update); }
  addEventListener('scroll', schedule, {passive: true});
  addEventListener('resize', schedule);
  addEventListener('hashchange', schedule);
  new ResizeObserver(schedule).observe(document.querySelector('.ltx_page_content'));
  schedule();
})();
</script>"""

# TeX drops the space after an operator where it breaks the line. A formula piece (see
# native_math) that ends its line hands that space back as a negative margin, so the operator
# meets the margin when the line is justified; CSS cannot see a line end. Where the shorter line
# would change a break, the line's word spaces take the operator's space instead: the line keeps
# its width and its breaks. Breaks never move, so pieces are taken in order. A piece wider than
# its column, with the text glued to it (unglue), is first boxed to scroll on its own.
TRIM_SCRIPT = """<script>
(function () {
  const piece = w => {  // the piece before a break, alone or in a span with its glued text
    const e = w.previousElementSibling;
    return e?.localName === 'math' ? e : e?.querySelector('math');
  };
  const wbrs = [...document.querySelectorAll('wbr')].filter(piece);
  const below = w => w.nextElementSibling.getBoundingClientRect().top
    >= w.previousElementSibling.getBoundingClientRect().bottom - .5;
  function blockOf(e) {
    while (/^(inline|contents)/.test(getComputedStyle(e).display)) e = e.parentElement;
    return e;
  }
  function widen(m, b, d) {  // the word spaces before m on its line, d px wider in all
    const M = m.getBoundingClientRect(), found = [];
    const walk = document.createTreeWalker(b, NodeFilter.SHOW_TEXT);
    for (let n; (n = walk.nextNode()) && !(n.compareDocumentPosition(m) & 2);) {
      if (n.parentElement.closest('math, [hidden]') || blockOf(n.parentElement) !== b) continue;
      for (let i = n.data.length - 1; i >= 0; i--) {
        if (!/[ \\n\\t\\u00a0]/.test(n.data[i])) continue;
        const r = document.createRange();
        r.setStart(n, i);
        r.setEnd(n, i + 1);
        const x = r.getBoundingClientRect();
        if (x.width > .01 && x.top < M.bottom && x.bottom > M.top) found.push([n, i]);
      }
    }
    return found.map(([n, i]) => {
      n.splitText(i + 1);
      const sp = n.splitText(i), s = document.createElement('span');
      s.className = 'arb-ws';
      s.style.wordSpacing = d / found.length + 'px';
      sp.replaceWith(s);
      s.append(sp);
      return s;
    });
  }
  function fit() {  // a piece wider than its column scrolls in its own box
    document.querySelectorAll('.arb-math-scroll').forEach(s => s.replaceWith(...s.childNodes));
    document.querySelectorAll('.ltx_page_main math').forEach(m => {
      if (m.closest('table')) return;  // displays and tables scroll whole
      let u = m;
      while (u.parentElement.matches('.arb-nobr, .arb-proof-end')) u = u.parentElement;
      const b = blockOf(u.parentElement), cs = getComputedStyle(b);
      if (u.getBoundingClientRect().width
          <= b.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight) + 1) return;
      const s = document.createElement('span');
      s.className = 'arb-math-scroll';
      u.replaceWith(s);
      s.append(u);
    });
  }
  function trim() {
    document.querySelectorAll('.arb-ws').forEach(s => s.replaceWith(...s.childNodes));
    document.body.normalize();
    wbrs.forEach(w => { w.previousElementSibling.style.marginInlineEnd = ''; });
    fit();
    const cut = [];
    for (let i = 0; i < wbrs.length; i++) {
      const w = wbrs[i], m = piece(w);
      if (!below(w)) continue;
      const b = blockOf(m.parentElement), top = m.getBoundingClientRect().top;
      const op = [...m.children].filter(k => k.localName !== 'mspace').pop();
      const d = m.getBoundingClientRect().right - op.getBoundingClientRect().right;
      if (d < .5) continue;
      const ok = () => below(w) && m.getBoundingClientRect().top === top
        && cut.every(k => !b.contains(wbrs[k]) || below(wbrs[k]));
      m.style.marginInlineEnd = -d + 'px';
      if (ok()) { cut.push(i); continue; }
      m.style.marginInlineEnd = '';
      const ws = widen(m, b, d);
      m.style.marginInlineEnd = -d + 'px';
      if (ws.length && ok()) { cut.push(i); continue; }
      m.style.marginInlineEnd = '';  // no word space on the line: left as it was
      ws.forEach(s => s.replaceWith(...s.childNodes));
    }
  }
  document.fonts.ready.then(trim);
  let timer;
  addEventListener('resize', function () { clearTimeout(timer); timer = setTimeout(trim, 200); });
})();
</script>"""

# The browser sets LaTeXML's MathML in Garamond-Math. The functions below bring that MathML to
# what TeX sets: LaTeXML spaces operators for its own dictionary, Chromium for MathML Core's.
OPEN, CLOSE = set("([{⟨⌊⌈|‖"), set(")]}⟩⌋⌉|‖")
# Operators MathML Core's dictionary has a prefix (postfix) entry for: an explicit form only
# repeats what Chromium infers for them, and Chromium drops its form fallback when the form is
# explicit, so nothing else is given one.
PREFIX, POSTFIX = OPEN | set("−+±∓¬∀∃∂∑∏∫⋃⋂"), CLOSE | set("!′″")
ORD = set("./⊥⊤∥")  # ordinary symbols in TeX that LaTeXML sets as operators
OP_ONLY = {"lspace", "rspace", "form", "fence", "separator", "accent", "largeop", "movablelimits"}
INVISIBLE_OPS = "⁡⁢⁣⁤"
MATH_RE = re.compile(r"<math\b([^>]*)>(.*?)</math>", re.S)
LEAF_RE = re.compile(r"<(mi|mn|mo|mtext|ms)\b[^>]*>([^<]*)</\1>")
INVISIBLE = dict.fromkeys(map(ord, "​" + INVISIBLE_OPS))


def mono(s):
    """Mathematical Monospace letters and digits (\\mathtt)."""
    return all(0x1D670 <= ord(c) <= 0x1D6A3 or 0x1D7F6 <= ord(c) <= 0x1D7FF for c in s)


# ASCII letters and digits to Mathematical Monospace, as LaTeXML writes most of a \mathtt constant
MONO = str.maketrans("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                     "".join(map(chr, [*range(0x1D7F6, 0x1D800), *range(0x1D670, 0x1D6A4)])))


def ascii_copy(m):
    """Pagefind ignores the MathML and indexes a hidden NFKC copy, so a search for ivk or
    GroupHash finds 𝗂𝗏𝗄 and 𝖦𝗋𝗈𝗎𝗉𝖧𝖺𝗌𝗁."""
    toks = [t for t in (unescape(x).translate(INVISIBLE).strip()
                        for _, x in LEAF_RE.findall(m.group(2))) if t]
    # a \mathtt literal ("z.cash:Orchard") stays one word: its letters are monospace tokens,
    # its punctuation plain tokens between them
    tt = [mono(t) or (t in ".:-_/" and 0 < i < len(toks) - 1 and mono(toks[i - 1])
                      and mono(toks[i + 1])) for i, t in enumerate(toks)]
    words = "".join(("" if i == 0 or tt[i] and tt[i - 1] else " ")
                    + unicodedata.normalize("NFKC", t) for i, t in enumerate(toks))
    words = re.sub(r"([(\[]) ", r"\1", re.sub(r" ([)\],])", r"\1", words))
    return (f'<math data-pagefind-ignore="all"{m.group(1)}>{m.group(2)}</math>'
            f'<span class="arb-idx" hidden> {escape(words, quote=False)} </span>')


def text_fixes(t):
    """Typography LaTeXML leaves to TeX's line breaker."""
    # LaTeXML keeps TeX's `` and '' as doubled single quotes inside a typewriter span.
    t = re.sub(r"(<span [^>]*ltx_font_typewriter[^>]*>)‘‘([^<]*)’’</span>", r"“\1\2</span>”", t)
    t = re.sub(r'<mtext class="ltx_mathvariant_monospace">‘‘([^<]*)’’</mtext>',
               r'<mtext>“</mtext><mtext class="ltx_mathvariant_monospace">\1</mtext>'
               r'<mtext>”</mtext>', t)
    # \, ("§\,5.4.1.6", "5\,kB") is a kern in TeX, never a break; LaTeXML writes U+2009, which
    # browsers break after, and EB Garamond has no U+202F, so the pair is kept whole. Tags,
    # titles, scripts and formulas are skipped whole.
    t = re.sub(r"(<math\b.*?</math>|<(title|script|style)\b.*?</\2>|<[^>]*>)"
               r"|([^\s<>;] [^\s<>&])",
               lambda m: m.group(1) or f'<span class="arb-nobr">{m.group(3)}</span>', t,
               flags=re.S)
    # No break between inline math and a hyphenated suffix ("64-byte"), closing punctuation (a
    # <math> is an atomic inline, which may break before a comma) or an opening bracket before
    # it; the formula's own break points stay (see unglue).
    return re.sub(r"([(\[]?)(<math\b[^>]*>(?:(?!</math>).)*</math>)(-[^\s<]+|[,.;:)\]]+)?",
                  lambda m: f'<span class="arb-nobr">{m.group(0)}</span>'
                  if m.group(1) or m.group(3) else m.group(0), t, flags=re.S)


def em(e, side):
    return float(e.get(side, "0em").removesuffix("em"))


def glue(width, op):
    """An operator's space, at its size."""
    size = {"mathsize": op.get("mathsize")} if op.get("mathsize") else {}
    return [ET.Element("mspace", {"width": f"{width:.3f}em"} | size)] if width else []


def tex_list(row):
    """LaTeXML's row as TeX's math list, in the encoding mathbreak reads (Temml's). LaTeXML nests a
    row per parsed subterm; TeX's list is flat, so nested rows open, an operator that led (ended)
    one first given the form it had there (a leading sign stays unary, a big operator is not a
    break). A word (lim, dim, the d of dx) is in no dictionary, so it takes the prefix form
    freely: TeX's Op or Ord, not a break; but \\bmod is a binary operator. A delimiter is a fence,
    never a break. A plain pair stays a row for pieces() to open; \\bigl( … \\bigr) opens (TeX's
    Open and Close atoms, flat in Temml); \\left … \\right stays shut. Invisible operators
    become their glue, ordinary symbols mi."""
    kids, out = list(row), []
    for i, k in enumerate(kids):
        c = k
        while c.tag in SCRIPTED and len(c):  # an embellished operator's form is its core's
            c = c[0]
        if c.tag == "mo" and "form" not in c.attrib and len(kids) > 1:
            word = c.text and c.text.isalpha() and not (
                c.text == "mod" and i > 0 and kids[i - 1].tag != "mo")
            if c.text in PREFIX and (i == 0 or c is not k) or word:  # a core leads its script
                c.set("form", "prefix")
            elif c.text in POSTFIX and i == len(kids) - 1 and c is k:
                c.set("form", "postfix")
        if k.tag == "mo" and k.text and k.text in INVISIBLE_OPS:
            out += glue(em(k, "lspace") + em(k, "rspace"), k)
        elif (k.tag == "mo" and (k.text in ORD or "monospace" in k.get("class", ""))
              and not {"stretchy", "minsize", "maxsize"} & k.attrib.keys()):  # unless sized
            mi = ET.Element("mi", {a: v for a, v in k.attrib.items() if a not in OP_ONLY})
            mi.text = k.text
            out += glue(em(k, "lspace"), k) + [mi] + glue(em(k, "rspace"), k)
        elif k.tag == "mrow" and len(k):
            ends = (k[0], k[-1])
            fenced = (all(e.tag == "mo" for e in ends) and k[0].text in OPEN
                      and k[-1].text in CLOSE)
            plain = fenced and all(e.get("stretchy") == "false" for e in ends)
            big = fenced and all(e.get("minsize") and e.get("minsize") == e.get("maxsize")
                                 for e in ends)
            if fenced and not (plain or big):
                out.append(k)
                continue
            inner = tex_list(k)
            if plain:
                k[:] = inner
                out.append(k)
            else:
                out += inner
        else:
            if k.tag == "mo" and k.text in (",", ";"):
                k.set("separator", "true")
            elif k.tag == "mo" and k.text in OPEN | CLOSE:
                k.set("fence", "true")
            out.append(k)
    return out


def mathml_fix(source, split=True):
    """One formula's MathML spaced as TeX spaces it; an inline formula outside a table is cut at
    TeX's break points into one <math> per piece, joined by <wbr>: Chromium breaks no formula
    itself, and justification stretches no space inside a piece."""
    root = ET.fromstring(source)
    for e in [e for e in root.iter() if e.tag in ("msup", "msubsup")]:
        # Garamond-Math's prime is drawn raised, as TeX's \prime is not: in a superscript it sat
        # small and high. Leading primes follow the base at its size (a′, a′ᵢ, y′²).
        sup = e[-1]
        lead = [sup] if sup.tag == "mo" else list(sup) if sup.tag == "mrow" else []
        primes = list(takewhile(lambda k: k.tag == "mo" and k.text and set(k.text) <= set("′″‴"),
                                lead))
        if not primes:
            continue
        for p in primes:
            p.attrib |= {"form": "postfix", "lspace": "0em", "rspace": "0em"}
        based = ET.Element("mrow")
        based.extend([e[0], *primes])
        rest = lead[len(primes):]
        if rest:
            sup[:] = rest
            e[0] = based
        elif e.tag == "msup":
            e.tag, e[:] = "mrow", list(based)
        else:
            e.tag, e[:] = "msub", [based, e[1]]
    in_script = set()
    for script in [e for e in root.iter() if e.tag in SCRIPTED]:
        # TeX sets no relation, binary or punctuation space in scripts ("i=0" under a sum)
        for child in list(script)[1:]:
            for mo in child.iter("mo"):
                mo.attrib.setdefault("lspace", "0em")
                mo.attrib.setdefault("rspace", "0em")
                in_script.add(mo)
    parent = {k: e for e in root.iter() for k in e}
    for tok in [e for e in root.iter() if "monospace" in e.get("class", "")
                and e.text and "\u2009" in e.text and not len(e)]:
        # \, in a \mathtt constant: LaTeXML writes U+2009 into the token, which the mono sets
        # 0.39 em wide; TeX's \, is 0.167 em. A piece of letters and digits takes the Unicode
        # monospace its neighbours have: Firefox maps mathvariant to it in the text mono, which
        # lacks it, so the piece fell back to another face and size.
        # In a row the pieces replace the token: Firefox spaces an invisible times beside an mrow.
        tag, attrs, parts = tok.tag, dict(tok.attrib), tok.text.split("\u2009")
        plain = {k: v for k, v in attrs.items() if k not in ("class", "mathvariant")}
        bits = []
        for i, part in enumerate(parts):
            if i:
                bits.append(ET.Element("mspace", {"width": "0.167em"}))
            if part and part.isascii() and part.isalnum():
                bits.append(ET.Element(tag, plain))
                bits[-1].text = part.translate(MONO)
            elif part:
                bits.append(ET.Element(tag, attrs))
                bits[-1].text = part
        row = parent.get(tok)
        if row is not None and row.tag in ("mrow", "math"):
            i = list(row).index(tok)
            row[i:i + 1] = bits
        else:
            tok.tag, tok.text = "mrow", None
            tok.attrib.clear()
            tok[:] = bits
    for tok in root.iter("mi"):
        # Firefox spaces a multi-letter identifier like an operator name beside an invisible
        # times; a run of a \mathtt constant is text
        if tok.text and len(tok.text) > 1 and mono(tok.text):
            tok.tag = "mtext"
    for over in root.iter("mover"):
        # \vec: LaTeXML's accent is a full-size → (wider than its base); TeX's is U+20D7
        if over.get("accent") == "true" and over[-1].tag == "mo" and over[-1].text == "→":
            over[-1].text = "⃗"
    for row in root.iter():
        kids = list(row)
        for prev, k, nxt in zip(kids, kids[1:], kids[2:]):
            # a \mathtt literal ("z.cash:Orchard-gd") is one mono word, as \texttt: the
            # punctuation between its letters is set tight and in the mono
            if (k.tag in ("mo", "mtext") and k.text in tuple(".:-_/") and prev.text and nxt.text
                    and mono(prev.text) and mono(nxt.text)):
                k.set("class", "ltx_mathvariant_monospace")
                if k.tag == "mo":
                    k.attrib |= {"lspace": "0em", "rspace": "0em"}
    for mo in root.iter("mo"):
        if mo.text in (",", ";") and mo not in in_script and mo.get("rspace") == "0em":
            # LaTeXML drops a comma's space before an operator ({0,⊥}, (⋅,⋅)); TeX sets a thin
            # space after punctuation in text style whatever follows
            del mo.attrib["rspace"]
        elif mo.text == ".":  # ordinary in TeX ("Sig.Sign"); LaTeXML spaces it as punctuation
            mo.attrib |= {"lspace": "0em", "rspace": "0em"}
        elif mo.text in ("/", "⊥", "⊤"):  # ordinary symbols in TeX; Core spaces them as operators
            mo.attrib.setdefault("lspace", "0em")
            mo.attrib.setdefault("rspace", "0em")
        elif mo.text == ":=":  # LaTeXML put the space before it on the left atom
            mo.attrib.setdefault("lspace", "0em")
        elif mo.text == "∥":  # \| is ordinary in TeX; LaTeXML adds a relation's space to \,
            for side in ("lspace", "rspace"):
                space = float(mo.get(side, "0.278em").removesuffix("em")) - 0.278
                mo.set(side, f"{max(space, 0):.3f}em")
    if root.get("display") != "inline" or not split:
        return ET.tostring(root, encoding="unicode", short_empty_elements=False)
    out = []
    for i, piece in enumerate(pieces(tex_list(root)) or [[]]):
        math = ET.Element("math", root.attrib if i == 0 else
                          {k: v for k, v in root.attrib.items() if k not in ("id", "alttext")})
        math.extend(piece)
        out.append(math)

    def text(es):
        return "".join("".join(e.itertext()) for e in es).translate(
            dict.fromkeys(map(ord, INVISIBLE_OPS)))
    if text(out) != text([root]):
        raise ValueError(f"formula split lost text: {source[:200]}")
    return "<wbr>".join(ET.tostring(p, encoding="unicode", short_empty_elements=False)
                        for p in out)


def native_math(t):
    """Every formula on a page through mathml_fix. One in a table or display row stays one
    <math>: Chromium breaks at <wbr> whatever the white-space, and there a formula keeps to one
    line."""
    tables, depth, start = [], 0, 0
    for tag in re.finditer(r"<(/?)table\b", t):
        depth += -1 if tag.group(1) else 1
        if depth == 1 and not tag.group(1):
            start = tag.start()
        elif depth == 0:
            tables.append((start, tag.end()))
    return re.sub(r"<math\b.*?</math>",
                  lambda m: mathml_fix(m.group(0),
                                       not any(a < m.start() < b for a, b in tables)),
                  t, flags=re.S)


NOWRAP = ('<span class="arb-nobr">', '<span class="arb-proof-end">')


def unglue(t):
    """Only Chromium breaks at a <wbr> inside a nowrap span. A span gluing text to a split formula
    (text_fixes, the proof's last formula) is cut at the formula's break points, so it glues the
    text to the adjacent piece alone."""
    out, spans = [], []
    for tok in re.split(r"(<span\b[^>]*>|</span>|<wbr>)", t):
        if tok.startswith("<span"):
            spans.append(tok)
        elif tok == "</span>":
            spans.pop()
        elif tok == "<wbr>":
            glued = list(takewhile(NOWRAP.__contains__, reversed(spans)))[::-1]
            tok = "</span>" * len(glued) + tok + "".join(glued)
        out.append(tok)
    t = "".join(out)
    for _ in NOWRAP:  # a piece cut from its glued text needs no span (twice: the spans nest)
        t = re.sub(r'<span class="arb-(?:nobr|proof-end)">(<math\b(?:(?!</math>).)*</math>)</span>',
                   r"\1", t, flags=re.S)
    return t

TIKZ_RE = re.compile(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", re.S)
PROOF_MATH_END_RE = re.compile(
    r'(<math\b(?:(?!</math>)[\s\S])*?</math>)([.!?])(?=\s*∎</p>)')
THEOREM_TITLE_RE = re.compile(
    r'(<div\b(?=[^>]*\bid="([^"]+)")'
    r'(?=[^>]*\bclass="[^"]*\bltx_theorem\b[^"]*")[^>]*>\s*'
    r'<h6\b[^>]*>)(.*?)(</h6>)', re.S)
UNEXPANDED_CREF_RE = re.compile(r"\\[Cc]ref[A-Za-z]*")
HTML_ID_RE = re.compile(r'''\sid\s*=\s*(["'])(.*?)\1''')
SECTION_HEADING_RE = re.compile(
    r'(<section\b[^>]*>\s*<h[1-6]\b)([^>]*)(>)')
DROP_IN_STANDALONE = ("\\documentclass", "\\usepackage[margin",
                      "\\renewenvironment{abstract}", "\\title{",
                      "\\author{", "\\date{",
                      "\\small\\begin{center}", "}{\\par\\medskip}")

# The PDF design preamble (fontspec + unicode-math + polyglossia, framed
# rules + fancyhdr) shares the following font block across volumes. LaTeXML
# uses classic TeX; the web build styles theorems and fonts in CSS. webprep
# swaps back to the classic package line, plus the identity macros the
# stripped design block provides. Keep these constants in sync with the
# volumes.
FONT_BLOCK = """\\usepackage{amsmath,amsthm,mathtools}
\\usepackage{fontspec}
\\usepackage[mathsf=sym]{unicode-math}
\\setmainfont{EBGaramond}[Path=fonts/, Extension=.otf,
  UprightFont=*-Regular, ItalicFont=*-Italic,
  BoldFont=*-Bold, BoldItalicFont=*-BoldItalic,
  FontFace={sb}{n}{*-SemiBold}, Numbers=Lining,
  SmallCapsFeatures={LetterSpace=4}]
% no sans text face in the family: \\textsf (crate names) is code, in the mono
\\defaultfontfeatures[Iosevka]{Path=fonts/, Extension=.ttf,
  UprightFont=*-Regular, ItalicFont=*-Italic, BoldFont=*-Bold,
  FontFace={sb}{n}{*-SemiBold}, Scale=MatchLowercase}
\\setsansfont{Iosevka}
\\setmonofont{Iosevka}
% stylistic set 3: the calligraphic \\mathcal (the default is a roundhand
% script). This copy maps capitals shared with Greek to the Latin, so copy
% and search see Latin (fonts/README-Garamond-Math.txt)
\\setmathfont{Garamond-Math-Latin.otf}[Path=fonts/, StylisticSet=3]
% the math sans is 6 % larger-eyed than the text; scaled to the text x-height
\\setmathfont{Garamond-Math-Latin.otf}[Path=fonts/,
  range=\\mathsfup/{latin,Latin,num}, Scale=0.94]
% each \\mathsf is one atom, as with a classic math alphabet, so a subscripted
% identifier such as \\rivk takes a further subscript
\\AtBeginDocument{\\let\\arbsymsf\\mathsf\\protected\\def\\mathsf#1{{\\arbsymsf{#1}}}}
\\usepackage{polyglossia}
\\setmainlanguage[variant=british,ordinalmonthday=false]{english}
\\PolyglossiaSetup{english}{frenchspacing=true}
"""
FONT_CLASSIC = ("\\usepackage{amsmath,amssymb,amsthm,mathtools}\n"
                "\\providecommand{\\accession}{}\n")
DESIGN_BLOCK_RE = re.compile(
    r"% kind-coded theorem blocks.*?"
    r"\\renewcommand\{\\sectionmark\}\[1\]\{[^\n]*\}\n",
    re.S)


def volumes_present():
    return [v for v in VOLUMES if (ROOT / f"{v}.tex").exists()]


def preamble_of(text):
    return text.split("\\begin{document}")[0]


def heading_anchors(text):
    """Give LaTeXML section headings Pagefind anchors, retaining section IDs."""
    used = {unescape(m.group(2)) for m in HTML_ID_RE.finditer(text)}

    def heading(match):
        # LaTeXML puts each section's heading directly inside its section.
        section_id = HTML_ID_RE.search(match.group(1))
        if not section_id or HTML_ID_RE.search(match.group(2)):
            return match.group(0)
        base = unescape(section_id.group(2)) + "-heading"
        name, suffix = base, 2
        while name in used:
            name = f"{base}-{suffix}"
            suffix += 1
        used.add(name)
        return (match.group(1) + match.group(2)
                + f' id="{escape(name, quote=True)}">')

    return SECTION_HEADING_RE.sub(heading, text)


def drop_subtitle(text):
    """A title page shows the volume's name alone; the landing and the PDF carry the subtitle."""
    return re.sub(r'(<h1 class="ltx_title ltx_title_document"[^>]*>\s*'
                  r'<span class="ltx_text ltx_font_bold"[^>]*>)(.*?)\s*<br class="ltx_break"\s*/?>\s*'
                  r'(</span>).*?(</h1>)', r'\1\2\3\4', text, count=1, flags=re.S)


def heading_self_links(text):
    """Make authored titles shareable without changing their text or targets."""
    used = {unescape(m.group(2)) for m in HTML_ID_RE.finditer(text)}

    def link(body, identifier):
        return (f'<a class="arb-heading-link" href="#{escape(identifier)}" '
                f'title="Link to this heading">{body}</a>')

    def theorem(match):
        start, identifier, body, end = match.groups()
        if 'class="arb-heading-link"' in body:
            return match.group(0)
        body = re.sub(r'<a\b[^>]*class="arb-permalink"[^>]*>.*?</a>',
                      '', body, flags=re.S)
        if re.search(r'<a\b', body):
            # Preserve citations inside a title rather than nesting anchors.
            body += ('<a class="arb-permalink" data-pagefind-ignore '
                     f'href="#{identifier}" aria-label="Permalink to this item" '
                     'title="Permalink">#</a>')
        else:
            body = link(body, unescape(identifier))
        return start + body + end

    text = THEOREM_TITLE_RE.sub(theorem, text)

    def heading(match):
        tag, attrs, body = match.groups()
        # a title page's name and subtitle stay plain text
        if re.search(r'<a\b', body) or 'ltx_title_document' in attrs:
            return match.group(0)
        identifier = HTML_ID_RE.search(attrs)
        if identifier:
            identifier = unescape(identifier.group(2))
        else:
            kind = re.search(r'\bltx_title_(part|section)\b', attrs)
            if not kind:
                return match.group(0)
            base = kind.group(1) + '-heading'
            identifier, suffix = base, 2
            while identifier in used:
                identifier, suffix = f'{base}-{suffix}', suffix + 1
            used.add(identifier)
            attrs += f' id="{escape(identifier)}"'
        return f'<{tag}{attrs}>' + link(body, identifier) + f'</{tag}>'

    return re.sub(r'<(h[1-6])\b([^>]*)>(.*?)</\1>', heading, text, flags=re.S)


def math_search_text(math):
    """Read the simple MathML forms used in headings without losing scripts."""
    def read(node):
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in {"math", "mrow", "mi", "mn", "mo", "mtext"}:
            return (node.text or "") + "".join(
                read(child) + (child.tail or "") for child in node)
        if tag == "mspace":
            return " "
        if tag in {"msub", "msup", "msubsup"}:
            parts = [read(child) for child in node]
            if len(parts) == (3 if tag == "msubsup" else 2):
                sub = f"_({parts[1]})" if tag != "msup" else ""
                sup = f"^({parts[-1]})" if tag != "msub" else ""
                base = parts[0]
                if node[0].tag.rsplit("}", 1)[-1] not in {"mi", "mn", "mo", "mtext"}:
                    base = f"({base})"
                return base + sub + sup
        raise ValueError(f"unsupported heading MathML: {tag}")

    try:
        return read(ET.fromstring(math))
    except (ET.ParseError, ValueError):
        # ponytail: complex expressions use their existing TeX alternative;
        # extend only for a new heading form that needs readable search text.
        alt = re.search(r'''\balttext=(["'])(.*?)\1''', math, re.S)
        if alt:
            return unescape(alt.group(2))
        raise ValueError("heading MathML needs an alttext fallback")


def heading_search_titles(text):
    """Supply complete search titles: Pagefind's anchor text omits MathML."""
    def heading(match):
        attrs, body, end = match.groups()
        heading_id = HTML_ID_RE.search(attrs)
        if (not heading_id or "<math" not in body
                or 'data-pagefind-meta="heading-' in attrs):
            return match.group(0)
        # a finished page's formulas carry a hidden search copy (ascii_copy)
        plain = re.sub(r'<math\b.*?</math>|<span class="arb-idx" hidden>[^<]*</span>',
                       lambda m: escape(math_search_text(m.group(0)))
                       if m.group(0).startswith('<math') else '',
                       body, flags=re.S)
        # NFKC: a search for ivk finds the heading's 𝗂𝗏𝗄
        title = unicodedata.normalize(
            "NFKC", " ".join(unescape(re.sub(r'<[^>]+>', '', plain)).split()))
        metadata = f"heading-{unescape(heading_id.group(2))}:{title}"
        return attrs + f' data-pagefind-meta="{escape(metadata)}">' + body + end

    return re.sub(
        r'(<h[1-6]\b[^>]*?)>(.*?)(</h[1-6]>)', heading, text, flags=re.S)


def reference_key(text, exact=False):
    """Ignore typography, but not words, when matching authored titles."""
    text = unicodedata.normalize('NFKC', text).casefold()
    # ZIP 244 distinguishes "TxId Digest" from "txid_digest".
    return ' '.join(text.split()) if exact else ''.join(c for c in text if c.isalnum())


SPEC_URL = 'https://zips.z.cash/protocol/protocol.pdf'
# Cited titles and their verified named destinations. Repeated specification
# titles require explicit source links; do not guess between abstract/concrete.
SPEC_SECTIONS = {
    'Shielded Pools and Notes': 'notes',
    'Mainnet and Testnet': 'networks',
    'The Block Chain': 'blockchain',
    'Transactions and Treestates': 'transactions',
    'Action Transfers and their Descriptions': 'actions',
    'Action Descriptions': 'actiondesc',
    'Action Statement (Orchard)': 'actionstatement',
    'Action Description Encoding and Consensus': 'actionencodingandconsensus',
    'Constants': 'constants',
    'Integers, Bit Sequences, and Endianness': 'endian',
    'Pallas and Vesta': 'pallasandvesta',
    'Coordinate Extractor for Pallas': 'concreteextractorpallas',
    'Group Hash into Pallas and Vesta': 'concretegrouphashpallasandvesta',
    'Orchard Key Components': 'orchardkeycomponents',
    'Sending Notes (Orchard)': 'orchardsend',
    'Dummy Notes (Orchard)': 'orcharddummynotes',
    'Note Plaintexts and Memo Fields': 'noteptconcept',
    'Encodings of Note Plaintexts and Memo Fields': 'noteptencoding',
    'Note Commitments': 'notecommitmentconcept',
    'Note Commitment Trees': 'notecommitmenttrees',
    'Merkle Path Validity': 'merklepath',
    'Nullifiers': 'nullifierconcept',
    'Nullifier Sets': 'nullifierset',
    'Commitment': 'abstractcommit',
    'Sinsemilla Hash Function': 'concretesinsemillahash',
    'Sinsemilla commitments': 'concretesinsemillacommit',
    'Homomorphic Pedersen commitments (Sapling and Orchard)': 'concretehomomorphiccommit',
    'Balance and Binding Signature (Orchard)': 'orchardbalance',
    'Chain Value Pool Balances': 'chainvaluepoolbalances',
    'BLAKE2 Hash Functions': 'concreteblake2',
    'RedDSA, RedJubjub, and RedPallas': 'concretereddsa',
    'Binding Signature (Sapling and Orchard)': 'concretebindingsig',
    'Signature with Re-Randomizable Keys': 'abstractsigrerand',
    'Zero-Knowledge Proving System': 'abstractzk',
    'Key Derivation': 'abstractkdf',
    'Orchard Key Agreement': 'concreteorchardkeyagreement',
    'Orchard Key Derivation': 'concreteorchardkdf',
    'Encryption (Sapling and Orchard)': 'saplingandorchardencrypt',
    'In-band secret distribution (Sapling and Orchard)': 'saplingandorchardinband',
    'Decryption using an Incoming Viewing Key (Sapling and Orchard)': 'decryptivk',
    'Decryption using an Outgoing Viewing Key (Sapling and Orchard)': 'decryptovk',
    'Transaction Encoding and Consensus': 'txnencoding',
    'Transaction Consensus Rules': 'txnconsensus',
    'Coinbase Transactions': 'coinbasetransactions',
    'Faerie Gold attack and fix': 'faeriegold',
    'Computing ρ values and Nullifiers': 'rhoandnullifiers',
    'DiversifyHashSapling and DiversifyHashOrchard Hash Functions': 'concretediversifyhash',
    'MerkleCRHOrchard Hash Function': 'orchardmerklecrh',
    'PoseidonHash Function': 'poseidonhash',
}
ZIP_SECTIONS = {
    0: {'Abstract': 'abstract', 'ZIP Status Field': 'zip-status-field'},
    32: {'Orchard internal key derivation': 'orchard-internal-key-derivation'},
    200: {'Activation mechanism': 'activation-mechanism',
          'Consensus rule set': 'terminology', 'Terminology': 'terminology',
          'Specification': 'specification'},
    203: {'Specification': 'specification'},
    209: {'Specification': 'specification', 'Terminology': 'terminology'},
    212: {'Motivation': 'motivation'},
    213: {'Specification': 'specification'},
    218: {'Anchor selection depth': 'anchorselectiondepth',
          'Block target spacing': 'blocktargetspacing',
          'Default expiry delta': 'defaultexpirydelta',
          'Shielded pool action limits': 'shieldedpoolactionlimits'},
    229: {'Transaction Format': 'transactionformat',
          'Consensus Rules': 'consensusrules',
          'Transaction Identifiers, Auth Digests, and Signature Digests':
              'transactionidentifiersauthdigestsandsignaturedigests',
          'Ironwood Component Digest': 'ironwoodcomponentdigest',
          'Anchor Commitment (Version 6)': 'anchorcommitmentversion6',
          'Summary of the resulting digest structure': 'summaryoftheresultingdigeststructure',
          'Reuse of the Orchard protocol with minimal changes':
              'reuseoftheorchardprotocolwithminimalchanges',
          'Separate state': 'separatestate',
          'enableCrossAddress polarity': 'enablecrossaddresspolarity',
          'Non-requirements': 'non-requirements',
          'Abstract': 'abstract', 'Terminology': 'terminology', 'Rationale': 'rationale',
          'Motivation': 'motivation'},
    244: {'TxId Digest': 'txid-digest', 'txid_digest': 'txid-digest-1',
          'Digests': 'digests', 'Authorizing Data Commitment': 'authorizing-data-commitment',
          'Signature Digest': 'signature-digest', 'T.1: header_digest': 't-1-header-digest',
          'T.2: transparent_digest': 't-2-transparent-digest',
          'T.3: sapling_digest': 't-3-sapling-digest',
          'T.4: orchard_digest': 't-4-orchard-digest',
          'S.2: transparent_sig_digest': 's-2-transparent-sig-digest',
          'A.3: orchard_auth_digest': 'a-3-orchard-auth-digest'},
    258: {'Consensus rules from NU6.3 activation': 'consensusrulesfromnu6.3activation',
          'Changes to the Protocol Specification': 'changestotheprotocolspecification',
          'ZIP 2005 activation': 'zip2005activation', 'Abstract': 'abstract'},
    259: {'Backward Compatibility': 'backwardcompatibility',
          'Rationale for no new transaction format': 'rationalefornonewtransactionformat',
          'Abstract': 'abstract', 'Rationale': 'rationale'},
    315: {'Anchor selection': 'anchor-selection',
          'Rationale for anchor selection': 'rationale-for-anchor-selection'},
    317: {'Fee calculation': 'fee-calculation'},
    326: {'Rationale for key-generation restrictions': 'rationaleforkey-generationrestrictions',
          'Fabricated same-address outputs and randomized note ciphertexts':
              'fabricatedsame-addressoutputsandrandomizednoteciphertexts'},
    2003: {'Specification': 'specification', 'Abstract': 'abstract',
           'Interaction with the proposed Network Sustainability Mechanism':
               'interaction-with-the-proposed-network-sustainability-mechanism'},
    2005: {'Abstract': 'abstract', 'Rationale': 'rationale',
           'Changes to the Protocol Specification': 'changestotheprotocolspecification',
           'Proposed Recovery Protocol': 'proposedrecoveryprotocol',
           'Repairing note commitments': 'repairingnotecommitments',
           'Attacks against binding of note commitments': 'attacksagainstbindingofnotecommitments'},
}


class ReferenceText(HTMLParser):
    """Visible text with source offsets, so adding links preserves the HTML."""
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.lines = [0] + [m.end() for m in re.finditer('\n', source)]
        self.text = ''
        self.positions = []
        self.parents = []
        self.feed(source)

    def source_offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if tag not in {'br', 'hr', 'img', 'input', 'meta', 'link', 'wbr', 'source'}:
            self.parents.append((tag, self.source_offset()))

    def handle_endtag(self, tag):
        for i in range(len(self.parents) - 1, -1, -1):
            if self.parents[i][0] == tag:
                del self.parents[i:]
                break

    def handle_data(self, data):
        start, parents = self.source_offset(), tuple(self.parents)
        self.text += data
        self.positions.extend((start + i, start + i + 1, parents)
                              for i in range(len(data)))

    def handle_entityref(self, name):
        raw = '&' + name + ';'
        value = unescape(raw)
        start = self.source_offset()
        self.text += value
        self.positions.extend((start, start + len(raw), tuple(self.parents))
                              for _ in value)

    def handle_charref(self, name):
        self.handle_entityref('#' + name)

    def link_range(self, start, end):
        positions = self.positions[start:end]
        if (not positions or positions[0][2] != positions[-1][2]
                or any(tag in {'a', 'code', 'pre', 'script', 'style'}
                       for _, _, parents in positions for tag, _ in parents)):
            return None
        return positions[0][0], positions[-1][1]


def reference_index(out):
    """Index actual generated headings, separately for each reading edition."""
    guides, sections = {}, {}
    for number, volume in enumerate(VOLUMES, 1):
        title = reference_key(vol_title(volume)[0])
        for edition, paths, home in (
                ('standalone', (out / volume).glob('*.html'), f'{volume}/'),
                ('complete', (out / 'complete').glob(f'V{number}.S*.html'),
                 f'complete/Pt{number}.html')):
            home_path = out / home / 'index.html' if home.endswith('/') else out / home
            if not home_path.is_file():
                continue
            guides[edition, title] = home
            targets = sections.setdefault((edition, title), {})
            objects = {}
            for page in paths:
                source = heading_anchors(page.read_text())
                headings = []
                for match in re.finditer(r'<h[1-6]\b([^>]*)>(.*?)</h[1-6]>', source, re.S):
                    attrs, body = match.groups()
                    if not re.search(r'\bltx_title_(?:section|subsection|subsubsection|paragraph)\b', attrs):
                        continue
                    heading_id = HTML_ID_RE.search(attrs)
                    headings.append((body, unescape(heading_id.group(2)) if heading_id else '', targets))
                headings.extend((match.group(3), unescape(match.group(2)), objects)
                                for match in THEOREM_TITLE_RE.finditer(source))
                for body, identifier, entries in headings:
                    body = re.sub(r'<span\b[^>]*class="[^"]*\bltx_tag\b[^"]*"[^>]*>.*?</span>',
                                  '', body, flags=re.S)
                    key = reference_key(ReferenceText(body).text)
                    href = page.relative_to(out).as_posix()
                    if identifier:
                        href += '#' + identifier
                    # Repeated titles such as "Syntax" are not unique targets.
                    entries[key] = href if key not in entries else None
            # A definition may repeat its section's name; section citations
            # still refer to the section, not the definition inside it.
            for key, href in objects.items():
                targets.setdefault(key, href)
    for edition in ('standalone', 'complete'):
        sources = [('specification', SPEC_URL, SPEC_SECTIONS)]
        sources += [(f'zip:{number}', f'https://zips.z.cash/zip-{number:04}', titles)
                    for number, titles in ZIP_SECTIONS.items()]
        for context, url, titles in sources:
            guides[edition, context] = url
            sections[edition, context] = {
                reference_key(title, exact=context.startswith('zip:')): url + '#' + anchor
                for title, anchor in titles.items()}
    return guides, sections


REFERENCE_RE = re.compile(
    r'(?P<guide>\b(?:[A-Z][A-Za-z]*|Halo\s+2)\s+Guide\b)'
    r'|(?P<external>\bZIP[\s-]*\d+\b|\b(?i:protocol\s+specification)\b)'
    r'|(?P<local>\b(?:this|next|previous) section\b)'
    r'|(?P<title>(?:§\s*)?[“"](?P<name>[^”"]+)[”"])'
    r'|(?P<unquoted>§(?=\s*[A-Za-z]))'
    r'|(?P<zipsection>\b(?:Abstract|Terminology|Motivation|Rationale|Specification)\b)')


def link_references(text, volume, index, current=None):
    """Link explicit citations, without guessing across paragraph bounds."""
    guides, sections = index
    edition = 'complete' if volume == 'complete' else 'standalone'
    current = (reference_key(vol_title(current or volume)[0])
               if current or volume != 'complete' else None)

    def block(match):
        source = match.group(0)
        # A formula's hidden search copy (ascii_copy) cites nothing; blanking keeps the offsets.
        parsed = ReferenceText(re.sub(r'(<span class="arb-idx" hidden>)([^<]*)',
                                      lambda m: m.group(1) + ' ' * len(m.group(2)), source))
        guide, paragraph, links = None, None, []
        consumed = 0
        for citation in REFERENCE_RE.finditer(parsed.text):
            href = None
            start, end = citation.span()
            if start < consumed:
                continue
            parent = next((parent for parent in reversed(parsed.positions[start][2])
                           if parent[0] == 'p'), None)
            if parent != paragraph:
                guide, paragraph = None, parent
            if any(tag in {'code', 'pre', 'script', 'style', 'math'}
                   for tag, _ in parsed.positions[start][2]):
                continue
            if citation.lastgroup == 'guide':
                guide = reference_key(citation.group())
                href = guides.get((edition, guide))
            elif citation.lastgroup == 'external':
                number = re.search(r'\d+', citation.group())
                guide = f'zip:{int(number.group())}' if number else 'specification'
                href = (f'https://zips.z.cash/zip-{int(number.group()):04}'
                        if number else SPEC_URL)
            elif citation.lastgroup == 'local':
                guide = current
            elif citation.lastgroup == 'unquoted':
                context = guide if guide is not None else current
                targets = sections.get((edition, context), {})
                for stop in range(end + 1, len(parsed.text) + 1):
                    key = reference_key(parsed.text[end:stop],
                                        exact=bool(context and context.startswith('zip:')))
                    if key and not any(title.startswith(key) for title in targets):
                        break
                    if (key in targets and parsed.text[stop - 1].isalnum()
                            and (stop == len(parsed.text) or not parsed.text[stop].isalnum())):
                        href, span_end = targets[key], stop
                if href:
                    end = span_end
            elif citation.lastgroup == 'zipsection':
                if guide and guide.startswith('zip:'):
                    href = sections.get((edition, guide), {}).get(
                        reference_key(citation.group(), exact=True))
            else:
                context = guide if guide is not None else (
                    current if citation.group().startswith('§') else None)
                href = sections.get((edition, context), {}).get(
                    reference_key(citation.group('name'),
                                  exact=bool(context and context.startswith('zip:'))))
            if href:
                # An unquoted title can contain another citation token.
                consumed = end
                if span := parsed.link_range(start, end):
                    start, end = span
                    links.append((start, end, href if href.startswith('https://') else '../' + href))
        for start, end, href in reversed(links):
            source = (source[:start] + f'<a class="arb-crossref" href="{escape(href)}">'
                      + source[start:end] + '</a>' + source[end:])
        return source

    return re.sub(r'<(?P<block>p|figcaption|td)\b[^>]*>.*?</(?P=block)>',
                  block, text, flags=re.S)


def render():
    FIGDIR.mkdir(parents=True, exist_ok=True)
    DEF_STARTS = ("\\newlength", "\\settowidth", "\\setlength",
                  "\\newcommand", "\\pgfmath")
    for vol in volumes_present():
        text = (ROOT / f"{vol}.tex").read_text()
        pics = list(TIKZ_RE.finditer(text))
        if not pics:
            continue
        labels = []
        if any("\\ref{" in pic.group(0) for pic in pics):
            with tempfile.TemporaryDirectory() as td:
                subprocess.run([
                    "tectonic", "-Z", "shell-escape", "--keep-intermediates",
                    "--outdir", td, str(ROOT / f"{vol}.tex"),
                ], cwd=ROOT, check=True, capture_output=True)
                aux = (Path(td) / f"{vol}.aux").read_text()
                labels = [
                    "\\expandafter\\def\\csname r@" + key
                    + "\\endcsname{{" + value + "}{}{}{Doc-Start}{}}"
                    for key, value in re.findall(
                        r"^\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux, re.M)
                ]
        pre_lines = [
            ln for ln in preamble_of(text).splitlines()
            if not any(ln.lstrip().startswith(d) for d in DROP_IN_STANDALONE)
        ]
        for i, m in enumerate(pics, 1):
            # carry along length/macro definitions the enclosing figure
            # environment sets up for this picture
            before = text[:m.start()]
            figpos = before.rfind("\\begin{figure}")
            defs = []
            if figpos != -1 and "\\end{figure}" not in before[figpos:]:
                defs = [ln for ln in before[figpos:].splitlines()
                        if ln.lstrip().startswith(DEF_STARTS)]
            doc = "\n".join(
                ["\\documentclass[tikz,border=2pt]{standalone}"]
                + pre_lines + ["\\begin{document}", "\\pagestyle{empty}"]
                + labels + defs
                + [m.group(0), "\\end{document}"])
            # the standalone compiles in a temp dir, so the volume's
            # repo-relative font path must become absolute
            doc = doc.replace("Path=fonts/", f"Path={ROOT}/fonts/")
            with tempfile.TemporaryDirectory() as td:
                tex = Path(td) / "fig.tex"
                tex.write_text(doc)
                subprocess.run(["tectonic", "-Z", "shell-escape", str(tex)],
                               cwd=td, check=True, capture_output=True)
                out = FIGDIR / f"{vol}-fig{i}.svg"
                subprocess.run(["pdftocairo", "-svg", str(Path(td) / "fig.pdf"),
                                str(out)], check=True)
                # PNG twin: LaTeXML's graphics handler rejects .svg includes
                subprocess.run(["pdftoppm", "-png", "-r", "180", "-singlefile",
                                str(Path(td) / "fig.pdf"),
                                str(FIGDIR / f"{vol}-fig{i}")], check=True)
                print(f"rendered {out.relative_to(ROOT)} (+ .png)")


def webprep():
    WEBDIR.mkdir(parents=True, exist_ok=True)
    for vol in volumes_present():
        text = (ROOT / f"{vol}.tex").read_text()
        n = [0]

        def sub(_m, vol=vol, n=n):
            n[0] += 1
            return (r"\includegraphics[width=0.9\linewidth]"
                    f"{{figures/{vol}-fig{n[0]}.png}}")

        text = TIKZ_RE.sub(sub, text)
        text = text.replace("\\author{m@rek.onl}", "\\author{}")
        if FONT_BLOCK in text:
            text = text.replace(FONT_BLOCK, FONT_CLASSIC, 1)
        text = DESIGN_BLOCK_RE.sub("", text, count=1)
        # PDF-only frame pagination; the website uses CSS theorem blocks.
        text = text.replace(r"\mdfsetup{nobreak=true}", "")
        lines = []
        for ln in text.splitlines():
            s = ln.lstrip()
            if s.startswith("\\usepackage{tikz}"):
                # tikz transitively provides xcolor, which \definecolor and
                # hyperref's colour options need; keep that half
                lines.append("\\usepackage{xcolor}")
            elif s.startswith("\\usetikzlibrary"):
                continue
            else:
                lines.append(ln)
        text = "\n".join(lines)
        if "\\usepackage{graphicx}" not in text:
            text = text.replace("\\usepackage{booktabs,enumitem}",
                                "\\usepackage{booktabs,enumitem}\n"
                                "\\usepackage{graphicx}", 1)
        (WEBDIR / f"{vol}.tex").write_text(text)
        print(f"prepared {WEBDIR / (vol + '.tex')}")
    omnibus(WEBDIR, WEBDIR / "arboretum-complete.tex")


ROMANS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
          "XI", "XII", "XIII", "XIV", "XV"]


def vol_title(vol):
    text = (ROOT / f"{vol}.tex").read_text()
    m = re.search(r"\\title\{\\textbf\{\\Huge ([^}]*)\}\\\\\[6pt\]"
                  r"\\large ([^}]*)\}", text)
    return (m.group(1) if m else vol, m.group(2) if m else "")


def ver():
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True,
                          cwd=ROOT).stdout.strip() or "0"


def page_head(title):
    """The head of a page at the site root."""
    return f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="icon" href="favicon.svg" type="image/svg+xml">
{THEME_INIT}
<link rel="stylesheet" href="arboretum.css?v={ver()}">"""


MACRO_RE = re.compile(r"\\(?:re)?newcommand\{(\\[A-Za-z]+)\}(\[\d\])?\{(.*)\}\s*$")


def design_lines(pre):
    """Lines of the PDF design block, shared by every part of the complete
    edition, its \\renewcommand lines included."""
    m = DESIGN_BLOCK_RE.search(pre)
    return set(m.group(0).splitlines()) if m else set()


def omnibus(srcdir=ROOT, out=None):
    """Generate arboretum-complete.tex: every volume as a \\part of one
    document. Mechanical: shared preamble (packages etc. deduped, macros
    stripped), per-part counter resets + the volume's own macros as \\def
    (volumes may use different macro bodies), per-volume label prefixing."""
    srcdir = Path(srcdir)
    out = Path(out) if out else ROOT / "arboretum-complete.tex"
    # LaTeXML's native IDs ignore hyperref's theH... macros. Prefix their
    # section root so all descendant IDs survive the per-volume resets.
    web_ids = ("\n\\makeatletter\n"
               "\\def\\thesection@ID{V\\arabic{arbvolume}.S\\@section@ID}\n"
               "\\makeatother" if srcdir == WEBDIR else "")
    vols = [v for v in VOLUMES if (srcdir / f"{v}.tex").exists()]
    seen, macro_free = set(), []
    for vol in vols:
        pre = preamble_of((srcdir / f"{vol}.tex").read_text())
        shared = design_lines(pre)
        for ln in pre.splitlines():
            s = ln.strip()
            if (not s or s.startswith(("\\title{", "\\author{", "\\date{"))
                    or MACRO_RE.match(s) and ln not in shared):
                continue
            # a later volume's \makeatletter region must keep its own pair
            if ln not in seen or s in ("\\makeatletter", "\\makeatother"):
                seen.add(ln)
                macro_free.append(ln)
    parts = ["\n".join(macro_free),
             "\\setcounter{tocdepth}{1}",
             "\\title{\\textbf{\\Huge The Zcash Arboretum}\\\\[6pt]"
             "\\large Foundations, deployed protocol, and frontier designs}",
             ("\\author{}\n\\date{}" if srcdir == WEBDIR
              else "\\author{m@rek.onl}\n\\date{}"),
             "\\newcounter{arbvolume}\n"
             "\\renewcommand*{\\theHsection}{\\arabic{arbvolume}.\\arabic{section}}\n"
             "\\renewcommand*{\\theHsubsection}{\\theHsection.\\arabic{subsection}}\n"
             "\\renewcommand*{\\theHsubsubsection}{\\theHsubsection.\\arabic{subsubsection}}\n"
             "\\renewcommand*{\\theHparagraph}{\\theHsubsubsection.\\arabic{paragraph}}\n"
             "\\renewcommand*{\\theHtheorem}{\\theHsection.\\arabic{theorem}}\n"
             "\\renewcommand*{\\theHequation}{\\theHsection.\\arabic{equation}}\n"
             "\\renewcommand*{\\theHfigure}{\\arabic{arbvolume}.\\arabic{figure}}\n"
             "\\renewcommand*{\\theHtable}{\\arabic{arbvolume}.\\arabic{table}}"
             + web_ids,
             "\\begin{document}\n\\maketitle",
             "\\clearpage\n\\tableofcontents\n\\clearpage",
             OMNIBUS_INTRO]
    for vol in vols:
        text = (srcdir / f"{vol}.tex").read_text()
        title, sub = vol_title(vol)
        short = vol.replace("-guide", "")
        # the running head names the part; \accession comes with the macros
        macros = [f"\\def\\arbvolname{{{title}}}"]
        shared = design_lines(preamble_of(text))
        for ln in preamble_of(text).splitlines():
            m = MACRO_RE.match(ln.strip())
            if m and ln not in shared:
                name, nargs, body = m.group(1), m.group(2), m.group(3)
                args = "".join(f"#{i+1}" for i in range(int(nargs[1:-1]))) \
                    if nargs else ""
                macros.append(f"\\def{name}{args}{{{body}}}")
        body = text.split("\\begin{document}", 1)[1].rsplit("\\end{document}", 1)[0]
        for drop in ("\\maketitle", "\\tableofcontents"):
            body = body.replace(drop + "\n", "").replace(drop, "")
        body = re.sub(r"(\\clearpage\s*)+", "\n", body, count=2)
        if srcdir == WEBDIR:
            body = body.replace("\\begin{abstract}", "").replace(
                "\\end{abstract}", "")
        body = re.sub(
            r"(\\(?:label|ref|eqref|pageref|autoref|cref|Cref)\{)([^}]+)\}",
            lambda m: m.group(1) + ",".join(
                f"{short}:{x.strip()}" for x in m.group(2).split(",")) + "}",
            body)
        body = re.sub(r"(\\hyperref\[)([^\]]+)\]",
                      lambda m: f"{m.group(1)}{short}:{m.group(2)}]", body)
        parts.append(
            "\\clearpage\n"
            "\\stepcounter{arbvolume}\n"
            "\\setcounter{section}{0}\\setcounter{equation}{0}"
            "\\setcounter{figure}{0}\\setcounter{table}{0}\n"
            f"\\part{{{title}: {sub}}}\n" + "\n".join(macros) + "\n" + body)
    parts.append("\\end{document}")
    out.write_text("\n".join(parts))
    print(f"wrote {out} ({len(vols)} parts)")


def landing(outdir):
    groups, n = {}, 0
    for vol, group in VOLUME_META:
        if not (ROOT / f"{vol}.tex").exists():
            continue
        title, sub = vol_title(vol)
        n += 1
        groups.setdefault(group, []).append(f"""<li class="plate">
<div class="label"><span class="acc">{ROMANS[n - 1]}</span></div>
<a class="title" href="{vol}/">{title}</a>
<p class="sub">{sub}</p>
<div class="links"><a href="pdf/{vol}.pdf" aria-label="{title}, PDF">PDF</a></div></li>""")
    cards = []
    for group, items in groups.items():
        cards.append(f'<h2 class="grp">{group}</h2>\n<p class="gloss">{GROUP_GLOSS[group]}</p>'
                     '<ol class="plates">' + "\n".join(items) + "</ol>")
    complete = f"""<h2 class="grp whole">Complete edition</h2><ol class="plates">
<li class="plate">
<div class="label"><span class="acc">I–{ROMANS[n - 1]}</span></div>
<a class="title" href="complete/">The Complete Arboretum</a>
<p class="sub">The nine volumes in one, in reading order</p>
<div class="links"><a href="pdf/arboretum-complete.pdf" aria-label="The Complete Arboretum, PDF">PDF</a></div></li>
</ol>"""
    html = f"""{page_head("The Zcash Arboretum")}
<link href="pagefind/pagefind-ui.css" rel="stylesheet">
<script src="pagefind/pagefind-ui.js"></script>
</head><body>
<main class="arb-landing">
<div class="arb-heading"><h1>The Zcash Arboretum</h1></div>
<p class="tag">Non-normative documentation of the deployed Zcash protocol
and designs being built on top of it. The
<a href="https://zips.z.cash/protocol/protocol.pdf">protocol specification</a>,
applicable ZIPs, and consensus rules remain authoritative.</p>
<div id="search"></div>
<script>
window.addEventListener('DOMContentLoaded', () => {{
  new PagefindUI({{ element: '#search', {SEARCH_OPTIONS} }});
}});
</script>
{chr(10).join(cards)}
{complete}
<footer class="foot">
{THEME_MENU}
<p><a href="concordance.html">Concordance</a></p>
<p>Spotted an error?
<a href="https://github.com/upbqdn/zcash-arboretum/issues/new">Open an issue</a>.</p>
</footer>
</main>
{PAGE_SCRIPT}
</body></html>
"""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    comp = ROOT / "arboretum-complete.pdf"
    if comp.exists():
        (out / "pdf").mkdir(parents=True, exist_ok=True)
        shutil.copy(comp, out / "pdf" / comp.name)
    (out / "index.html").write_text(html)
    print(f"wrote {out / 'index.html'}")


def tex_text(s):
    """A section title's LaTeX as plain HTML text: commands unwrapped, dollars and ties gone."""
    s = re.sub(r"\\(?:emph|textit|textbf|mathrm|mathsf|mathbb|mathcal|texttt)\{([^{}]*)\}", r"\1", s)
    s = s.replace("\\S", "&sect;").replace("--", "&ndash;").replace("~", " ").replace("$", "")
    return re.sub(r"\\[A-Za-z]+\s*", "", s)


def concordance(outdir):
    """ZIP and protocol-specification sections -> the volume sections that treat them."""
    import collections
    zips = collections.defaultdict(set)
    specs = collections.defaultdict(set)
    order = {vol: n for n, (vol, _g) in enumerate(VOLUME_META)}
    for vol, _g in VOLUME_META:
        p = ROOT / f"{vol}.tex"
        if not p.exists():
            continue
        title, _ = vol_title(vol)
        sec = (0, "Front matter")  # LaTeXML names the n-th section's page Sn.html
        prev = ""
        for ln in p.read_text().splitlines():
            if ln.lstrip().startswith("%"):
                continue
            m = re.match(r"\\section\{([^}]*)\}", ln.strip())
            if m:
                sec = (sec[0] + 1, m.group(1))
            for z in re.findall(r"ZIP[-~ ]?(\d{2,4})\b", ln):
                zips[int(z)].add((vol, title) + sec)
            # protocol-spec sections; skip cross-volume cites ("... Guide"
            # on the same line) and internal \S\ref uses
            if not re.search(r"\\emph\{[^}]*Guide", prev + " " + ln):
                for sp in re.findall(r"\\S[~ ]?(\d+(?:\.\d+)+)", ln):
                    specs[tuple(int(x) for x in sp.split("."))].add((vol, title) + sec)
            prev = ln

    def places(refs):
        """One line per volume, in reading order: the italic name, then its sections."""
        by_vol = collections.defaultdict(list)
        for vol, title, n, sec in refs:
            by_vol[(order[vol], vol, title)].append((n, sec))
        lines = []
        for (_o, vol, title), secs in sorted(by_vol.items()):
            links = "; ".join(f'<a href="{vol}/{f"S{n}.html" if n else ""}">{tex_text(s)}</a>'
                              for n, s in sorted(set(secs)))
            lines.append(f'<p><em>{title}</em>: {links}</p>')
        return "".join(lines)

    rows = [f'<tr><td class="zk"><a href="https://zips.z.cash/zip-{z:04d}">ZIP {z}</a></td>'
            f'<td>{places(zips[z])}</td></tr>' for z in sorted(zips)]
    srows = [f'<tr><td class="zk">&sect; {".".join(map(str, sp))}</td>'
             f'<td>{places(specs[sp])}</td></tr>' for sp in sorted(specs)]
    html = f"""{page_head("Concordance &mdash; The Zcash Arboretum")}
</head><body>
<main class="arb-landing zc">
<p class="up"><a href="./">The Zcash Arboretum</a></p>
<div class="arb-heading"><h1>Concordance</h1></div>
<p class="tag">Every ZIP and protocol-specification section cited across
the volumes, and the sections that treat it. Generated from the sources.</p>
<h2>ZIPs</h2>
<table>{"".join(rows)}</table>
<h2>Protocol specification</h2>
<table>{"".join(srows)}</table>
<footer class="foot">
{THEME_MENU}
<p><a href="./">The Zcash Arboretum</a></p>
<p>Spotted an error?
<a href="https://github.com/upbqdn/zcash-arboretum/issues/new">Open an issue</a>.</p>
</footer>
</main>
{PAGE_SCRIPT}
</body></html>"""
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    (out / "concordance.html").write_text(html)
    print(f"concordance: {len(zips)} ZIPs, {len(specs)} spec sections")


def postprocess(outdir):
    """Ensure the complete edition exists, then finish every HTML page."""
    out = Path(outdir)
    complete = out / "complete"
    if not (complete / "index.html").is_file():
        subprocess.run([
            "latexmlc", f"--dest={complete / 'index.html'}",
            "--splitat=section", "--format=html5",
            "--navigationtoc=context", "--css=../arboretum.css",
            "--timeout=1800", "build/web/arboretum-complete.tex",
        ], cwd=ROOT, check=True)
    # The accession numeral: a volume's place in the reading order; the edition takes the range.
    documents = [(vol, vol_title(vol)[0], vol, ROMANS[i])
                 for i, (vol, _group) in enumerate(VOLUME_META)]
    documents.append(("complete", "The Complete Arboretum",
                      "arboretum-complete", f"I–{ROMANS[len(VOLUME_META) - 1]}"))
    references = reference_index(out)
    reading_order = 0
    for vol, title, pdf, acc in documents:
        vdir = out / vol
        if not vdir.is_dir():
            continue
        # The numeral has its own span so phones keep it; a Contents disclosure stands in for
        # the sidebar where there is no room for it.
        bar = f"""<header class="arb-bar"><a class="wordmark" href="../"><span
class="wordmark-prefix">The Zcash </span>Arboretum</a><a class="volname" href="./#arb-contents"
title="{acc} {title}: contents"><span class="arb-acc">{acc}</span><span
class="arb-volname"> {title}</span></a>
<details class="arb-toc"><summary>Contents</summary></details>
<details class="arb-search"><summary>Search</summary>
<div class="arb-search-panel"><div id="arb-search-ui"></div></div></details>
<a class="arb-pdf" href="../pdf/{pdf}.pdf">PDF</a>
{THEME_MENU}
</header>
<link href="../pagefind/pagefind-ui.css" rel="stylesheet">
<script src="../pagefind/pagefind-ui.js"></script>
<script>
(function () {{
  const search = document.querySelector('details.arb-search');
  search.querySelector('summary').addEventListener('click', function (e) {{
    e.preventDefault();
    search.open = !search.open;
    if (search.open && !window.__arbSearch) {{
      window.__arbSearch = new PagefindUI({{ element: '#arb-search-ui',
        {SEARCH_OPTIONS} }});
    }}
    // Keep focus in the user gesture so touch keyboards can open too.
    if (search.open)
      search.querySelector('.pagefind-ui__search-input').focus();
  }});
  document.addEventListener('click', function (e) {{
    // Pagefind can remove the clicked load-more button before this bubbles.
    if (!e.composedPath().includes(search)) search.open = false;
    if (e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey
        && e.target.closest('.arb-search a.pagefind-ui__result-link'))
      search.open = false;
  }});
  document.addEventListener('keydown', function (e) {{
    if (e.key === 'Escape' && search.open) {{
      if (search.contains(e.target))
        search.querySelector('summary').focus();
      search.open = false;
    }}
  }});
}})();
</script>"""
        n = 0
        pages = sorted(vdir.glob("*.html"), key=lambda p: (
            p.name != "index.html",
            [int(part) if part.isdigit() else part
             for part in re.split(r"(\d+)", p.name)]))
        for page in pages:
            reading_order += 1
            t = page.read_text()
            if match := UNEXPANDED_CREF_RE.search(t):
                raise RuntimeError(
                    f"{page}: unexpanded cross-reference macro {match.group()}")
            part = re.match(r'(?:V|Pt)(\d+)', page.stem) if vol == 'complete' else None
            current = VOLUMES[int(part.group(1)) - 1] if part else None
            t2 = heading_self_links(heading_anchors(t))
            t2 = link_references(heading_search_titles(t2), vol, references, current)
            if page.name == "index.html":
                t2 = drop_subtitle(t2)
                t2 = t2.replace('<nav class="ltx_TOC ltx_list_toc ltx_toc_toc">',
                                '<nav id="arb-contents" '
                                'class="ltx_TOC ltx_list_toc ltx_toc_toc">', 1)
            t2 = t2.replace('class="arb-permalink" href=',
                            'class="arb-permalink" data-pagefind-ignore href=')
            if vol != "complete" and 'data-pagefind-meta="volume:' not in t2:
                t2 = re.sub(
                    r'(<[^>]+class="ltx_page_content"[^>]*)(>)',
                    lambda m: m.group(1) + ' data-pagefind-meta="volume:'
                    + escape(f"{acc} {title}", quote=True) + '">', t2, count=1)
            if vol != "complete":
                t2 = re.sub(r' data-pagefind-sort="reading-order:\d+"', '', t2)
                t2 = re.sub(
                    r'(<[^>]+class="ltx_page_content"[^>]*)(>)',
                    lambda m: m.group(1)
                    + f' data-pagefind-sort="reading-order:{reading_order}">',
                    t2, count=1)
            if 'data-arb="vol"' in t:
                if t2 != t:
                    page.write_text(t2)
                    n += 1
                continue
            # British hyphenation
            t2 = t2.replace('<html lang="en">', '<html lang="en-GB">', 1)
            t2 = re.sub(r'(<head[^>]*>)',
                        lambda m: m.group(1) + THEME_INIT, t2, count=1)
            # LaTeXML may copy CSS and emit a build-directory-relative URL.
            t2 = re.sub(r'href="(?:[^"]*/)?arboretum\.css(?:\?[^"]*)?"',
                        f'href="../arboretum.css?v={ver()}"', t2, count=1)
            # "3 Keys and addresses — V Ironwood Guide"
            t2 = re.sub(r"<title>(.*?)</title>",
                        lambda m: "<title>" + (m.group(1).split(" ‣ ")[0] + " — "
                                               if " ‣ " in m.group(1) else "")
                        + f"{acc} {title}</title>\n"
                        '<link rel="icon" href="../favicon.svg" type="image/svg+xml">',
                        t2, count=1, flags=re.S)
            t2 = re.sub(r"<body", '<body data-arb=\"vol\"', t2, count=1)
            if vol == "complete":
                t2 = re.sub(r"<body", '<body data-pagefind-ignore', t2,
                            count=1)
            t2 = re.sub(r"(<body[^>]*>)", r"\1" + bar.replace("\\", "\\\\"),
                        t2, count=1)
            if vol != "complete":
                t2 = t2.replace('class="ltx_page_content"',
                                'class="ltx_page_content" data-pagefind-body',
                                1)
            # PDF inside the navigation, shown where the bar has no room for it
            t2 = t2.replace('<nav class="ltx_page_navbar">',
                            '<nav class="ltx_page_navbar"><p class="arb-nav-tools">'
                            f'<a href="../pdf/{pdf}.pdf">PDF</a></p>', 1)
            # the Contents panel opens with "V Ironwood Guide", the subtitle on its own line
            t2 = re.sub(r'<a href="\./" title="" class="ltx_ref" rel="start">.*?</a>',
                        lambda m: '<a href="./" class="ltx_ref arb-start" rel="start">'
                        f'<span class="arb-acc">{acc}</span> {title}'
                        + "".join(f'<span class="arb-start-sub">{s}</span>' for s in
                                  re.findall(r"</span></span>(.*?)</span></a>", m.group(0),
                                             re.S)) + '</a>', t2, count=1, flags=re.S)
            t2 = re.sub(r'<div class="ltx_page_logo">.*?</div>\n?', '', t2, count=1,
                        flags=re.S)
            t2 = t2.replace(
                '</footer>',
                '<div class="arb-feedback">Spotted an error? '
                '<a href="https://github.com/upbqdn/zcash-arboretum/issues/new">'
                f'Open an issue</a>.</div>\n</footer>', 1)
            t2 = PROOF_MATH_END_RE.sub(
                r'<span class="arb-proof-end">\1\2</span>', t2)
            t2 = re.sub(r'\s*∎(?=</p>)',
                        ' <span class="arb-qed">□</span>', t2)
            t2 = text_fixes(t2)
            if vol != "complete":
                t2 = MATH_RE.sub(ascii_copy, t2)
            t2 = unglue(native_math(t2))
            # Figures load the committed SVG beside LaTeXML's PNG copy.
            for name in set(re.findall(r'<img src="build/web/figures/([^"/]+)\.png"', t2)):
                shutil.copy(FIGDIR / f"{name}.svg", vdir / "build/web/figures" / f"{name}.svg")
            t2 = re.sub(r'(<img src="build/web/figures/[^"/]+)\.png"', r'\1.svg"', t2)
            t2 = t2.replace('</body>', TRIM_SCRIPT + '\n' + PAGE_SCRIPT + '\n' + TOC_SCRIPT
                            + '\n</body>', 1)
            if t2 != t:
                page.write_text(t2)
                n += 1
        print(f"postprocessed {vol}: {n} pages")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "volumes":
        print(*VOLUMES)
    elif mode == "render":
        render()
    elif mode == "webprep":
        webprep()
    elif mode == "landing":
        landing(sys.argv[sys.argv.index("--out") + 1])
    elif mode == "concordance":
        concordance(sys.argv[sys.argv.index("--out") + 1])
    elif mode == "omnibus":
        omnibus()
    elif mode == "postprocess":
        postprocess(sys.argv[sys.argv.index("--out") + 1])
    else:
        sys.exit(__doc__)

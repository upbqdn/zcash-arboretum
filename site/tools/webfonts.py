#!/usr/bin/env python3
"""Build the site's webfonts into site/fonts. Run locally and commit the outputs (needs tectonic
and fontTools with brotli).

Usage: webfonts.py IOSEVKA_TTF

EB Garamond and Garamond-Math come from tectonic's bundle, the files the PDFs set; Iosevka is
Iosevka-Regular.ttf 34.8.1 from https://github.com/be5invis/Iosevka/releases.
"""

import io
import subprocess
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

OUT = Path(__file__).resolve().parents[1] / "fonts"
OFL = ("This Font Software is licensed under the SIL Open Font License, Version 1.1.",
       "https://openfontlicense.org/")
# Latin, IPA (the Math Guide's letter table), Greek and the punctuation the volumes set.
EB_GARAMOND = "U+0020-007E,U+00A0-03FF,U+1E00-1EFF,U+2000-206F,U+20AC,U+2190-2193,U+2212,U+25A1"
# Iosevka sets identifiers only.
IOSEVKA = "U+0020-007E,U+00A0-017F,U+2000-206F,U+2190-2193,U+2212"


def bundle(name):
    return TTFont(io.BytesIO(subprocess.run(["tectonic", "-X", "bundle", "cat", name],
                                            capture_output=True, check=True).stdout))


def cut(font, unicodes, features=None):
    """A subset with every name record; features None keeps fontTools' default list."""
    options = subset.Options(name_IDs=["*"])
    if features is not None:
        options.layout_features = features
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=subset.parse_unicodes(unicodes))
    subsetter.subset(font)
    return font


def save(font, name):
    """WOFF2 with the licence in the name table (IDs 13, 14), as the OFL asks."""
    font["name"].setName(OFL[0], 13, 3, 1, 0x409)
    font["name"].setName(OFL[1], 14, 3, 1, 0x409)
    font.flavor = "woff2"
    font.save(OUT / name)


def garamond_math():
    """Garamond-Math draws each Latin capital and its Greek look-alike with one glyph, so copied
    text reports the italic ones as Greek; this copy maps a shared italic glyph from the Latin
    only, as the PDFs' copy does. MathML Core drops a subscript by the base's depth plus
    SubscriptBaselineDropMin for every base, TeX only for boxes: at 150/1000 the p in y_p sat
    0.12 em below the PDF's, and 0 keeps a letter's subscript where TeX puts it."""
    font = bundle("Garamond-Math.otf")
    best, first = font.getBestCmap(), {}
    for cp in sorted(best):
        first.setdefault(best[cp], cp)
    greek = [cp for cp, g in best.items() if first[g] != cp and 0x1D6E2 <= cp <= 0x1D6FA]
    assert len(greek) == 13, greek
    for table in font["cmap"].tables:
        if table.isUnicode():
            for cp in greek:
                table.cmap.pop(cp, None)
    font["MATH"].table.MathConstants.SubscriptBaselineDropMin.Value = 0
    return font


def iosevka_math(path):
    """Iosevka's letters and digits at the Mathematical Monospace code points: \\mathtt in the
    text mono."""
    font = cut(TTFont(path), "U+0030-0039,U+0041-005A,U+0061-007A", features=[])
    ascii_cmap = font.getBestCmap()
    remap = {0x1D670 + i: ascii_cmap[0x41 + i] for i in range(26)}
    remap |= {0x1D68A + i: ascii_cmap[0x61 + i] for i in range(26)}
    remap |= {0x1D7F6 + i: ascii_cmap[0x30 + i] for i in range(10)}
    table = CmapSubtable.newSubtable(12)
    table.platformID, table.platEncID, table.language, table.cmap = 3, 10, 0, remap
    font["cmap"].tables = [table]
    font["name"].setName("Iosevka Math", 1, 3, 1, 0x409)
    return font


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    for style in ("Regular", "Italic", "SemiBold", "SemiBoldItalic"):
        save(cut(bundle(f"EBGaramond-{style}.otf"), EB_GARAMOND, features=["*"]),
             f"eb-garamond-{style.lower()}.woff2")
    save(garamond_math(), "garamond-math.woff2")
    save(cut(TTFont(sys.argv[1]), IOSEVKA), "iosevka.woff2")
    save(iosevka_math(sys.argv[1]), "iosevka-math.woff2")

"""Check the short deck's worked arithmetic and rendered content.

Run: python3 -B talks/check_short_slides.py [path/to/deck.pdf]
Requires pdftotext (Poppler); polynomial arithmetic uses only the stdlib.
These checks do not establish cryptographic security or inspect figure layout.
"""

from pathlib import Path
import re
import subprocess
import sys
import unicodedata


# Adapted from .wip/talk-rewrite/compute/g_toy.py; no runtime .wip dependency.
# Coefficients are listed from constant term to highest power, over F_97.
P = 97
# a, b, c, qM, qL, qR, qO, qC, PI: the two displayed tables combined.
ROWS = [
    (3, 3, 9, 1, 0, 0, -1, 0, 0),
    (9, 3, 27, 1, 0, 0, -1, 0, 0),
    (27, 3, 30, 0, 1, 1, -1, 0, 0),
    (30, 0, 0, 0, 1, 0, 0, 5, -35),
]


def trim(f):
    f = [coefficient % P for coefficient in f]
    while len(f) > 1 and f[-1] == 0:
        f.pop()
    return f


def add(f, g):
    result = [0] * max(len(f), len(g))
    for polynomial in (f, g):
        for i, coefficient in enumerate(polynomial):
            result[i] += coefficient
    return trim(result)


def scale(f, coefficient):
    return trim([coefficient * value for value in f])


def mul(f, g):
    result = [0] * (len(f) + len(g) - 1)
    for i, a in enumerate(f):
        for j, b in enumerate(g):
            result[i + j] += a * b
    return trim(result)


def evaluate(f, x):
    return sum(a * pow(x, i, P) for i, a in enumerate(f)) % P


def interpolate(points):
    result = [0]
    for i, (xi, yi) in enumerate(points):
        numerator, denominator = [1], 1
        for j, (xj, _) in enumerate(points):
            if i != j:
                numerator = mul(numerator, [-xj, 1])
                denominator = denominator * (xi - xj) % P
        result = add(result, scale(numerator, yi * pow(denominator, -1, P)))
    return result


def divide(f, g):
    remainder = trim(f)
    quotient = [0] * max(1, len(f) - len(g) + 1)
    while remainder != [0] and len(remainder) >= len(g):
        degree = len(remainder) - len(g)
        coefficient = remainder[-1] * pow(g[-1], -1, P) % P
        quotient[degree] = coefficient
        remainder = add(remainder, [0] * degree + scale(g, -coefficient))
    return trim(quotient), remainder


def check_arithmetic():
    assert (96 + 2) % P == 1
    assert pow(5, -1, P) == 39 and 5 * 39 % P == 1
    assert 3**3 + 3 + 5 == 35
    omega = 22
    domain = [pow(omega, i, P) for i in range(4)]
    assert domain == [1, 22, 96, 75]
    assert pow(omega, 2, P) == P - 1 and pow(omega, 4, P) == 1
    vanishing = [1]
    for h in domain:
        vanishing = mul(vanishing, [-h, 1])
    assert vanishing == [96, 0, 0, 0, 1]

    rows = ROWS
    for a, b, c, qm, ql, qr, qo, qc, pi in rows:
        assert (qm * a * b + ql * a + qr * b + qo * c + qc + pi) % P == 0
    assert rows[0][0] == rows[0][1] == rows[1][1] == rows[2][1]
    assert all(rows[i][2] == rows[i + 1][0] for i in range(3))

    def gate(trace):
        columns = [interpolate(list(zip(domain, column))) for column in zip(*trace)]
        for polynomial, column in zip(columns, zip(*trace)):
            assert [evaluate(polynomial, h) for h in domain] == [v % P for v in column]
        a, b, c, qm, ql, qr, qo, qc, pi = columns
        assert a == [90, 61, 22, 24]
        result = mul(mul(qm, a), b)
        for f, g in ((ql, a), (qr, b), (qo, c)):
            result = add(result, mul(f, g))
        return add(add(result, qc), pi)

    honest = gate(rows)
    quotient, remainder = divide(honest, vanishing)
    assert len(honest) - 1 == 9 and len(quotient) - 1 == 5
    assert remainder == [0] and mul(quotient, vanishing) == honest
    assert all(evaluate(honest, h) == 0 for h in domain)

    altered_rows = rows.copy()
    altered_rows[0] = (3, 3, 10, *rows[0][3:])
    altered = gate(altered_rows)
    bad_quotient, residual = divide(altered, vanishing)
    assert [evaluate(altered, h) for h in domain] == [96, 0, 0, 0]
    assert residual == [24, 24, 24, 24]
    assert add(mul(bad_quotient, vanishing), residual) == altered
    residues = [evaluate(residual, z) for z in range(P)]
    assert residues == [24 * (1 + z + z*z + z*z*z) % P for z in range(P)]
    assert [z for z, value in enumerate(residues) if value == 0] == [22, 75, 96]
    assert residues[20] == 53
    assert residues.count(0) == len(residual) - 1 == 3  # This cheat: 3/97.
    assert max(len(altered) - 1, 5 + len(vanishing) - 1) == 9  # General: 9/97.
    assert evaluate(vanishing, 20) == 46
    assert evaluate(quotient, 20) == 67
    assert evaluate(honest, 20) == 67 * 46 % P == 75
    assert evaluate(altered, 20) == 20
    assert evaluate(bad_quotient, 20) * 46 % P == 64
    assert (20 - 64) % P == 53
    print("PASS F97 inverse, trace, wiring, interpolation, quotient, roots and openings")


def check_pdf(pdf):
    text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    text = unicodedata.normalize("NFKC", text).replace("−", "-").replace("⋅", "·")
    pages = [page for page in text.split("\f") if page.strip()]
    assert 0 < len(pages) <= 40, f"Expected 1–40 slides, found {len(pages)}"
    assert not re.search(r"\bguide\b|\bsources?\s*:", text, re.I), "References leaked onto slides"
    normalised = " ".join(text.split())
    for phrase in (
        "Arithmetic with a modulus", "Why it hides", "Why it binds",
        "Membership without revealing the leaf", "copy constraints",
        "A nonzero polynomial has few roots", "Evaluation is an inner product",
        "Binding does not by itself give privacy", "Back to the transaction",
    ):
        assert phrase in normalised, f"Missing rendered content: {phrase}"
    compact = "".join(text.split())
    for formula in (
        "96+2=1", "5·39=1", "5-1=39", "H={1,22,96,75}",
        "a(X)=90+61X+22X2+24X3", "a(h)392730",
        "D(X)=24(1+X+X2+X3)≠0", "3·3-10=-1=96", "(20,53)",
        "75=67·46=75", "20≠64", "3/97", "9/97",
    ):
        assert formula in compact, f"Missing rendered arithmetic: {formula}"
    trace = next(page for page in pages if "Turn the computation into rows" in page)
    rendered_rows = re.findall(r"^\s*([0-3])\s+(\d+)\s+(\d+)\s+(\d+)\b", trace, re.M)
    assert [tuple(map(int, row)) for row in rendered_rows] == [
        (i, *row[:3]) for i, row in enumerate(ROWS)
    ], "Rendered trace differs from the checked arithmetic"
    selectors = next(page for page in pages if "One gate, selected differently" in page)
    rendered_selectors = re.findall(
        r"^\s*(0,\s*1|2|3)\s+(-?\d+(?:\s+-?\d+){5})\s*$", selectors, re.M)
    assert {"".join(label.split()): tuple(map(int, values.split()))
            for label, values in rendered_selectors} == {
        "0,1": ROWS[0][3:], "2": ROWS[2][3:], "3": ROWS[3][3:]
    }, "Rendered selectors differ from the checked arithmetic"
    # Prose-only proxy: isolated letters, indices and digits inflate math counts.
    # A warning is useful for review; it is not a layout or readability verdict.
    dense = [(i, len(re.findall(r"[A-Za-z]{2,}(?:['’][A-Za-z]+)?", page)))
             for i, page in enumerate(pages, 1)]
    for number, words in dense:
        if words > 90:
            print(f"WARNING slide {number}: {words} prose words; inspect density")
    print(f"PASS {len(pages)} rendered slides; no visible references; content and arithmetic present")


if __name__ == "__main__":
    check_arithmetic()
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name(
        "zcash-private-transactions-short.pdf")
    check_pdf(pdf)

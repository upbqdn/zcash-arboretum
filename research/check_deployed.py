#!/usr/bin/env python3
"""Independent exact-arithmetic checks for the deployed-volume audit.

No network, dependencies, or generated files. Reads the printed tables so
changing a displayed value changes the test, rather than merely reprinting
the original drafting scripts' calculations.
"""

from fractions import Fraction as F
from hashlib import blake2b
from math import comb
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
consensus = (ROOT / "consensus-guide.tex").read_text()


def risk(q, n):
    if q >= F(1, 2):
        return F(1)
    return 2 * sum(comb(m + n - 1, m) * q**n * (1 - q)**m
                   for m in range(n))


def rows(label):
    table = next(t for t in re.findall(
        r"\\begin\{table\}.*?\\end\{table\}", consensus, re.S
    ) if "\\label{" + label + "}" in t)
    return [(F(q, 100), row.split("&")) for q, row in
            ((int(q), row) for q, row in re.findall(
                r"\$(\d+)\\%\$\s*&\s*(.*?)\\\\", table, re.S))]


def number(cell):
    return F(cell.strip().strip("$").replace("{,}", ""))


cells = 0
for q, row in rows("tab:cons-r"):
    n = 1
    for cell in row:
        count = re.search(r"\\multicolumn\{(\d+)\}", cell)
        if count:
            count = int(count[1])
            for _ in range(count):
                actual = 100 * risk(q, n)
                assert actual == 100 if q == F(1, 2) else actual < F(1, 10**5)
                n += 1
                cells += 1
            continue
        value = cell.strip().strip("$").replace(r"\!", "")
        scientific = re.fullmatch(r"([\d.]+)\\cdot10\^\{(-?\d+)\}", value)
        if scientific:
            mantissa, exponent = scientific.groups()
            scale = F(10) ** int(exponent)
            expected = F(mantissa) * scale
            decimals = len(mantissa.partition(".")[2])
            tolerance = scale / (2 * 10**decimals)
        else:
            expected = F(value)
            tolerance = F(1, 2 * 10**len(value.partition(".")[2]))
        assert abs(100 * risk(q, n) - expected) <= tolerance, (q, n, cell)
        n += 1
        cells += 1
    assert n == 11
print(f"Probability table: {cells} cells, exact rational rounding/bounds pass")

cells = 0
for q, row in rows("tab:cons-nreq"):
    for cell, target in zip(row, (F(1, 10), F(1, 100), F(1, 1000)), strict=True):
        n = int(number(cell))
        assert risk(q, n) < target
        assert n == 1 or risk(q, n - 1) >= target
        cells += 1
print(f"Confirmation thresholds: {cells} cells, strict boundaries pass")

cells = 0
for q, row in rows("tab:cons-vmax"):
    for cell, n in zip(row, (1, 2, 4, 6, 8, 10), strict=True):
        r = risk(q, n)
        assert number(cell) == int(5 * (1 - r) / r), (q, n, cell)
        cells += 1
print(f"Subsidy-only heuristic profit table: {cells} exact floors pass")

# An independent binomial-tail expression checks the negative-binomial race.
for q in (F(1, 50), F(1, 10), F(1, 5), F(3, 10), F(12, 25)):
    for n in range(1, 21):
        tail = sum(comb(2*n-1, k) * q**k * (1-q)**(2*n-1-k)
                   for k in range(n, 2*n))
        assert risk(q, n) == 2 * tail
print("Race identity: 100 exact negative-binomial/binomial comparisons pass")

# Recompute F4Jumble round values using only the standard-library BLAKE2b.
wallet = (ROOT / "wallet-guide.tex").read_text()
trace = wallet.split(r"\begin{example}[A unified address, end to end]", 1)[1]
trace = trace.split(r"\end{example}", 1)[0]
values = re.findall(r"& ([0-9a-f]{60,62}) \\", trace)
assert len(values) == 6
a, b, expected_x, expected_y, expected_d, expected_c = map(bytes.fromhex, values)


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b, strict=True))


def h(i, data):
    return blake2b(data, digest_size=30,
                   person=b"UA_F4Jumble_H" + bytes((i, 0, 0))).digest()


def g(i, data):
    return blake2b(data, digest_size=64,
                   person=b"UA_F4Jumble_G" + bytes((i, 0, 0))).digest()[:31]


x = xor(b, g(0, a))
y = xor(a, h(0, x))
d = xor(x, g(1, y))
c = xor(y, h(1, d))
assert (x, y, d, c) == (expected_x, expected_y, expected_d, expected_c)
inverse_y = xor(c, h(1, d))
inverse_x = xor(d, g(1, inverse_y))
inverse_a = xor(inverse_y, h(0, inverse_x))
inverse_b = xor(inverse_x, g(0, inverse_a))
assert (inverse_a, inverse_b) == (a, b)
print("F4Jumble: all four printed rounds and inverse pass")

# Correct the old drafting script's 640-bit-input/512-bit-output confusion.
p = 0x40000000000000000000000000000000224698FC094CF91B992D30ED00000001
q = 0x40000000000000000000000000000000224698FC0994A8DD8C46EB2100000001
assert 2**254 < p < q < 2**255
assert pow(5, (p - 1) // 2, p) == p - 1
assert (2**512 + q - 1) // q < 2**258
assert 1 + 2 * 307 < 2**10
assert F(q, 2**512) < F(1, 2**257)
assert 1 + 11 + 8 + 32 == 52
assert 52 + 512 + 16 == 580
assert 1 + 32 + 32 + 8 + 32 + 32 == 137
assert 2720 + 2272 == 4992
assert 2_000_000 // 948 == 2109
assert 73_932_454 // 2**16 == 1128
assert 50_191_264 // 2**16 == 765
assert (1128 + 765) * 32 == 60576
assert 136378 + 5 * (1128 + 765) == 145843
assert 66 + 8 + 1 == 75 and 75 * 4 // 3 == 100
print("Field, invalid-key, ciphertext, proof, payment-cap and subtree arithmetic pass")

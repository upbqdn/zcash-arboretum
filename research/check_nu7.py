#!/usr/bin/env python3
"""Recompute NU7 guide examples using only the standard library.

Sources: ZIPs 218, 237 and 259 at zips afa086bd; proposed Ironwood
coverage in PR 1361 at 721fbcad. No activation height or reserve seed
is assigned here. The illustrative activation heights below are test inputs.
"""

from decimal import Decimal, localcontext
from fractions import Fraction as F
from math import comb
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def source(name):
    return (ROOT / name).read_text().replace("{,}", "")


consensus = source("consensus-guide.tex")
wallet = source("wallet-guide.tex")
compact = re.sub(r"\s+", "", consensus)


def ceildiv(n, d):
    return -(-n // d)


def risk(q, n):
    return 2 * sum(comb(m + n - 1, m) * q**n * (1 - q)**m
                   for m in range(n))


# Time and risk: counts buy the same modelled security, not equal money.
assert 30 * 60 // 25 == 72
assert 3 * 25 == 75 and 10 * 25 == 250
assert 120 * 25 == 3000 and 3000 // 60 == 50
assert 600 * 25 == 15000 and 15000 // 60 == 250
assert 100 * 25 == 2500 and 6 * 25 == 150
assert abs(F(539 * 25, 3600) - F("3.74")) < F("0.005")
assert abs(F(600 * 25, 3600) - F("4.17")) < F("0.005")
assert abs(F(100 * 25, 60) - F("41.7")) < F("0.05")
r72 = risk(F(1, 10), 72)
assert abs(r72 - F("9.35e-34")) < F("0.005e-34")
assert r"$9.35\times10^{-34}$" in consensus
assert risk(F(1, 10), 3) * 100 == F("1.712")
for equation in (r"600\cdot25=15000", r"100\cdot25=2500",
                 r"120\cdot25=3000", r"6\cdot25=150"):
    assert equation in compact, equation
print("NU7 timing and confirmation probabilities: exact checks pass")


# Target damping uses truncation towards zero; the floor precedes scaling.
timespan = 102 * 25
low, high = timespan * 84 // 100, timespan * 132 // 100
assert (timespan, low, high) == (2550, 2142, 3366)
assert r"T=N\cdot25=2550" in compact
assert "$2142$ and $3366$" in consensus
assert int(F(-1, 4)) == 0  # Not Python's negative integer floor division.
assert int(F(-5, 4)) == -1
assert 3000 // timespan * timespan == 2550
assert 3000 * timespan // timespan == 3000
assert r"\left\lfloor\frac{\overline{t}(h)}{T}\right\rfloorc(h)" in compact
print("NU7 difficulty window, clamps, and rounding order: checks pass")


def within_budget(orchard, ironwood, sapling):
    return (0 <= orchard <= 330 and 0 <= ironwood <= 330
            and 0 <= sapling <= 300 and orchard + ironwood + sapling <= 330)


assert within_budget(100, 200, 30)
assert not within_budget(100, 201, 30)
assert within_budget(0, 330, 0)
assert not within_budget(330, 330, 0)
assert not within_budget(0, 0, 301)
assert 330 // 2 == 165 and F(165, 25) == F("6.6")
assert r"O+I+S\leq330" in compact
blocks_per_day = 86400 // 25
actions_per_day = 330 * blocks_per_day
field_bytes = 3 * 32 + 52
# Four length-delimited fields, then a repeated-message tag and length.
message_bytes = field_bytes + 4 * 2
wire_bytes = message_bytes + 1 + 2
assert (blocks_per_day, actions_per_day, field_bytes, wire_bytes) == (
    3456, 1140480, 148, 159)
assert actions_per_day * field_bytes == 168791040
assert actions_per_day * wire_bytes == 181336320
for value in (3456, actions_per_day, 168791040, 181336320):
    assert str(value) in wallet, value
print("NU7 shared Action budget and compact scanning payloads: checks pass")


def halving(height, activation, blossom):
    return int(F(blossom - 10000, 840000)
               + F(activation - blossom, 1680000)
               + F(height - activation, 5040000))


def scheduled(height, activation, blossom):
    return 1250000000 // (6 * 2**halving(height, activation, blossom))


assert 1680000 * 3 == 5040000
for blossom, old_third in ((653600, 4406400), (584000, 4476000)):
    for activation in (3000000, 3543000, 4400000):
        third = activation + 3 * (old_third - activation)
        assert halving(third - 1, activation, blossom) == 2
        assert halving(third, activation, blossom) == 3
        assert halving(third + 5040000, activation, blossom) == 4
        assert scheduled(third - 1, activation, blossom) == 52083333
        assert scheduled(third, activation, blossom) == 26041666
assert 3 * 4406400 == 13219200
assert "s_h=52083333" in compact and "$26041666$" in consensus
assert "$0.52083333$" in consensus
assert 3 * 52083333 == 156250000 - 1  # Integer rounding is not exact issuance.
print("NU7 activation-aware halving schedule and subsidies: checks pass")


# Delayed reserve payout: current-block removals cannot fund this payout.
denominator = 10**10
numerator = 6931680000 // 5040000
assert numerator == 1375


def reserve_step(balance, removed, active=True):
    additional = ceildiv(numerator * balance, denominator) if active else 0
    return additional, balance - additional + removed


assert reserve_step(100000000, 0) == (14, 99999986)
assert reserve_step(100000000, 100000000) == (14, 199999986)
assert reserve_step(0, 100000000) == (0, 100000000)
assert reserve_step(100000000, 100000000, False) == (0, 200000000)
for balance in (0, 1, 2, 7272727, 7272728, 100000000, 21_000_000 * 10**8):
    for removed in (0, 1, 100000000):
        additional, after = reserve_step(balance, removed)
        assert 0 <= additional <= balance
        assert (additional > 0) == (balance > 0)
        issued_delta = 52083333 + additional - removed
        assert issued_delta + after - balance == 52083333
for number in (1375, 99999986, 199999986):
    assert str(number) in consensus, number
with localcontext() as context:
    context.prec = 50
    remaining = (1 - Decimal(numerator) / denominator)**5040000
    assert abs(remaining - Decimal("0.50007")) < Decimal("0.000005")
assert r"\approx0.50007" in consensus
print("NU7 reserve delay, integer payouts, conservation, and half-life: pass")


def varint(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return result.hex()


assert varint(0xD884B698) == "98ed92c40d"
assert varint(0x77190AD9) == "d995e4b807"
wallet_hex = re.sub(r"\s+", "", wallet)
assert "98ed92c40d" in wallet_hex and "d995e4b807" in wallet_hex
print("NU7 PCZT v6 group and branch identifier varints: pass")

# The three workshop decks share the probability-to-time illustrations.
for name in ("zcash-private-transactions", "zcash-workshop-screen",
             "zcash-workshop-whiteboard"):
    deck = re.sub(r"\s+", "", source(f"talks/{name}.tex"))
    for value in (r"9.35\times10^{-34}", "3.74", "4.17", "41.7"):
        assert value in deck, (name, value)
print("NU7 talk risk and elapsed-time values match the checked calculations")

for name in ("zcash-private-transactions", "zcash-workshop-screen"):
    deck = re.sub(r"\s+", "", source(f"talks/{name}.tex"))
    for percent in (5, 10, 20, 30, 40):
        values = []
        for n in (1, 2, 4, 6, 8, 10):
            probability = risk(F(percent, 100), n)
            values.append(int(4 * (1 - probability) / probability))
        row = f"${percent}\\%$&" + "&".join(f"${v}$" for v in values)
        assert row in deck, (name, percent)
print("Both full talk reward-normalised tables: 60 exact floors pass")

#!/usr/bin/env python3
"""Exact, dependency-free checks for the shared F97 and Sigma examples.

Run: python3 -B research/check_foundations.py
Polynomial coefficients are ascending, over F_97. These checks verify the
displayed algebra, not cryptographic hardness or complete protocol security.
"""

from fractions import Fraction
from itertools import product


P = 97
H = (1, 22, 96, 75)


def trim(a):
    a = [x % P for x in a]
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a


def add(a, b):
    out = [0] * max(len(a), len(b))
    for i, x in enumerate(a):
        out[i] += x
    for i, x in enumerate(b):
        out[i] += x
    return trim(out)


def scale(a, x):
    return trim([x * y for y in a])


def mul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return trim(out)


def evaluate(a, x):
    out = 0
    for coefficient in reversed(a):
        out = (out * x + coefficient) % P
    return out


def interpolate(values):
    out = [0]
    for i, value in enumerate(values):
        basis, denominator = [1], 1
        for j, x in enumerate(H):
            if i != j:
                basis = mul(basis, [-x, 1])
                denominator = denominator * (H[i] - x) % P
        out = add(out, scale(basis, value * pow(denominator, -1, P)))
    assert tuple(evaluate(out, x) for x in H) == tuple(v % P for v in values)
    return out


def divide(a, b):
    remainder = trim(a)
    quotient = [0] * max(1, len(a) - len(b) + 1)
    while remainder != [0] and len(remainder) >= len(b):
        degree = len(remainder) - len(b)
        coefficient = remainder[-1] * pow(b[-1], -1, P) % P
        quotient[degree] = coefficient
        remainder = add(remainder, [0] * degree + scale(b, -coefficient))
    return trim(quotient), remainder


def gate(columns):
    a, b, c, qm, ql, qr, qo, qc, pi = map(interpolate, columns)
    return add(add(add(mul(mul(qm, a), b), mul(ql, a)), mul(qr, b)),
               add(add(mul(qo, c), qc), pi))


def check_traces():
    assert tuple(pow(22, i, P) for i in range(4)) == H
    # One identical table is used by the Halo guide and companion talk.
    columns = [(3, 9, 27, 30), (3, 3, 3, 0), (9, 27, 30, 0),
               (1, 1, 0, 0), (0, 0, 1, 1), (0, 0, 1, 0),
               (-1, -1, -1, 0), (0, 0, 0, 5), (0, 0, 0, -35)]
    expected = ([90, 61, 22, 24], [75, 32, 25, 65], [65, 16, 3, 22])
    assert tuple(map(interpolate, columns[:3])) == expected
    vanishing = [-1, 0, 0, 0, 1]
    honest = gate(columns)
    quotient, remainder = divide(honest, vanishing)
    assert quotient == [61, 70, 43, 47, 81, 46] and remainder == [0]
    changed = list(columns)
    changed[2] = (10,) + columns[2][1:]
    dishonest = gate(changed)
    bad_quotient, remainder = divide(dishonest, vanishing)
    assert remainder == [24] * 4
    assert [x for x in range(P) if evaluate(remainder, x) == 0] == [22, 75, 96]
    assert evaluate(vanishing, 20) == 46
    assert evaluate(quotient, 20) == 67
    assert evaluate(honest, 20) == 75
    assert evaluate(dishonest, 20) == 20
    assert evaluate(bad_quotient, 20) * 46 % P == 64
    print(f"Guide and talk: quotient={quotient}; altered residual={remainder}")


def check_extractor():
    # Fresh row on every attempt; two independent challenges within that row.
    cases = 0
    for n in range(2, 9):
        kappa = Fraction(1, n)
        for counts in product(range(n + 1), repeat=3):
            deltas = [Fraction(count, n) for count in counts]
            epsilon = sum(deltas) / 3
            success = sum(delta * (delta - kappa) for delta in deltas) / 3
            assert success >= epsilon * (epsilon - kappa)
            if epsilon > kappa:
                assert success > 0
                assert 1 / success <= 1 / (epsilon * (epsilon - kappa))
            cases += 1
    print(f"Sigma extractor: {cases} exact acceptance-distribution cases")


if __name__ == "__main__":
    check_traces()
    check_extractor()
    print("Foundation trace and extraction checks passed")

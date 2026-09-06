#!/usr/bin/env python3
"""Exact, dependency-free regressions for the foundation audit.

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
    traces = {
        "guide": [(3, 9, 27, 30), (3, 3, 3, 0), (9, 27, 30, 0),
                  (1, 1, 0, 0), (0, 0, 1, 1), (0, 0, 1, 0),
                  (-1, -1, -1, 0), (0, 0, 0, 5), (0, 0, 0, -35)],
        "talk": [(3, 9, 27, 30), (3, 3, 3, 5), (9, 27, 30, 35),
                 (1, 1, 0, 0), (0, 0, 1, 1), (0, 0, 1, 1),
                 (-1, -1, -1, -1), (0, 0, 0, 0), (0, 0, 0, 0)],
    }
    vanishing = [-1, 0, 0, 0, 1]
    for name, columns in traces.items():
        honest = gate(columns)
        quotient, remainder = divide(honest, vanishing)
        assert remainder == [0] and len(quotient) == 6
        changed = list(columns)
        changed[2] = (10,) + columns[2][1:]
        dishonest = gate(changed)
        bad_quotient, remainder = divide(dishonest, vanishing)
        assert remainder == [24] * 4
        assert [x for x in range(P) if evaluate(remainder, x) == 0] == [22, 75, 96]
        assert evaluate(vanishing, 20) == 46
        if name == "guide":
            assert evaluate(quotient, 20) == 67
            assert evaluate(honest, 20) == 75
            assert evaluate(dishonest, 20) == 20
            assert evaluate(bad_quotient, 20) * 46 % P == 64
        print(f"{name}: quotient={quotient}; bad residual={remainder}; roots=3/97")


def check_extractor():
    # Exhaust every three-row acceptance matrix, up to challenge permutation,
    # for N=2..8. Include zero rows and one-accepting-challenge trap rows.
    cases = 0
    for n in range(2, 9):
        kappa = Fraction(1, n)
        for counts in product(range(n + 1), repeat=3):
            deltas = [Fraction(count, n) for count in counts]
            epsilon = sum(deltas) / 3
            if not kappa < epsilon < 1:
                continue
            a = b = Fraction(0)
            for delta in deltas:
                if delta == 0:
                    continue
                weight = delta / (3 * epsilon)
                success = (delta - kappa) / (1 - kappa)
                phase_end = success + (1 - success) * epsilon
                a += weight / phase_end
                b += weight * success / phase_end
            assert b > 0
            assert a / b <= (1 - kappa) / (epsilon - kappa)
            cases += 1
    print(f"Sigma extractor: {cases} exact row-distribution cases passed")


def check_ipa():
    # Free formal generators: compare every generator coefficient, rather than
    # use a tiny cyclic group whose accidental discrete-log relations hide bugs.
    for u, v in product(range(1, 12), repeat=2):
        a = [3, 9, 27, 30]
        bs = [pow(20, i, P) for i in range(4)]
        gs = [[int(i == j) for j in range(6)] for i in range(4)]
        h, extra = [0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 1]
        dot = lambda xs, ys: sum(x * y for x, y in zip(xs, ys)) % P
        combine = lambda xs, ys: [sum(x * y[j] for x, y in zip(xs, ys)) % P
                                  for j in range(6)]
        r = 17
        lhs = [(x + r * y + dot(a, bs) * z) % P
               for x, y, z in zip(combine(a, gs), h, extra)]
        for challenge in (u, v):
            inverse = pow(challenge, -1, P)
            half = len(a) // 2
            lo, hi = a[:half], a[half:]
            gl, gh, bl, bh = gs[:half], gs[half:], bs[:half], bs[half:]
            ell, rr = 13, 29
            left = [(x + ell * y + dot(lo, bh) * z) % P
                    for x, y, z in zip(combine(lo, gh), h, extra)]
            right = [(x + rr * y + dot(hi, bl) * z) % P
                     for x, y, z in zip(combine(hi, gl), h, extra)]
            lhs = [(x + challenge ** 2 * y + inverse ** 2 * z) % P
                   for x, y, z in zip(lhs, left, right)]
            a = [(challenge * x + inverse * y) % P for x, y in zip(lo, hi)]
            bs = [(inverse * x + challenge * y) % P for x, y in zip(bl, bh)]
            gs = [[(inverse * x + challenge * y) % P for x, y in zip(g, f)]
                  for g, f in zip(gl, gh)]
            r = (r + challenge ** 2 * ell + inverse ** 2 * rr) % P
        rhs = [(a[0] * x + r * y + a[0] * bs[0] * z) % P
               for x, y, z in zip(gs[0], h, extra)]
        assert lhs == rhs
    print("Symmetric IPA: 121 two-round formal-generator identities passed")


if __name__ == "__main__":
    check_traces()
    check_extractor()
    check_ipa()
    print("All foundation regressions passed")

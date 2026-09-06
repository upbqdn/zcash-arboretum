#!/usr/bin/env python3
"""Exact small-field checks for the rewritten Halo construction.

Run after integration: python3 -B research/check_halo2.py
Formal generator coefficients test identities without accidental tiny-group
discrete-log relations. These checks do not prove cryptographic security.
"""

from itertools import product

from check_foundations import P, add, divide, evaluate, mul, scale, trim


def interpolate_at(points, values):
    out = [0]
    for i, value in enumerate(values):
        numerator, denominator = [1], 1
        for j, point in enumerate(points):
            if i != j:
                numerator = mul(numerator, [-point, 1])
                denominator = denominator * (points[i] - point) % P
        out = add(out, scale(numerator, value * pow(denominator, -1, P)))
    assert [evaluate(out, x) for x in points] == [v % P for v in values]
    return out


def horner(polynomials, challenge):
    out = [0]
    for polynomial in polynomials:
        out = add(scale(out, challenge), polynomial)
    return out


def dot(a, b):
    return sum(x * y for x, y in zip(a, b)) % P


def combine(scalars, points):
    return [sum(s * point[i] for s, point in zip(scalars, points)) % P
            for i in range(len(points[0]))]


def check_ipa():
    cases = 0
    for n, xi, z in product((2, 4, 8), (1, 2, 7), (1, 13)):
        x, r, rs = 20, 17, 29
        p = [(i**3 + 3) % P for i in range(n)]
        s = [(7 * i + 5) % P for i in range(n)]
        s[0] = (s[0] - evaluate(s, x)) % P
        assert evaluate(s, x) == 0
        v = evaluate(p, x)
        a = [(a + xi * b) % P for a, b in zip(p, s)]
        a[0] = (a[0] - v) % P
        assert evaluate(a, x) == 0
        b = [pow(x, i, P) for i in range(n)]
        basis = [[int(i == j) for j in range(n + 2)]
                 for i in range(n + 2)]
        generators, w, extra = basis[:n], basis[n], basis[n + 1]
        blind = (r + xi * rs) % P
        lhs = combine(a + [blind], generators + [w])
        weights, challenges = [1], []
        for round_number in range(n.bit_length() - 1):
            challenge = 5 + round_number
            challenges.append(challenge)
            inverse = pow(challenge, -1, P)
            half = len(a) // 2
            al, ar = a[:half], a[half:]
            bl, br = b[:half], b[half:]
            gl, gr = generators[:half], generators[half:]
            ell, rho = 13 + round_number, 31 + round_number
            left = combine(ar + [z * dot(ar, bl), ell], gl + [extra, w])
            right = combine(al + [z * dot(al, br), rho], gr + [extra, w])
            lhs = combine([1, inverse, challenge], [lhs, left, right])
            a = [(l + inverse * r) % P for l, r in zip(al, ar)]
            b = [(l + challenge * r) % P for l, r in zip(bl, br)]
            generators = [combine([1, challenge], [l, r])
                          for l, r in zip(gl, gr)]
            blind = (blind + inverse * ell + challenge * rho) % P
            assert lhs == combine(a + [z * dot(a, b), blind],
                                  generators + [extra, w])
            factor = [1] + [0] * (n // 2**(round_number + 1) - 1) + [challenge]
            weights = mul(weights, factor)
        assert len(a) == len(b) == len(generators) == 1
        assert generators[0] == combine(weights, basis[:n])
        assert b[0] == evaluate(weights, x)
        if n == 4:
            u0, u1 = challenges
            assert weights == [1, u1, u0, u0 * u1 % P]
        cases += 1
    print(f"Asymmetric masked IPA: {cases} full formal-generator checks")


def check_multiopen():
    groups = [[[2, 3, 4], [7, 1, 9, 2]], [[5, 8, 1]], [[4, 2, 0, 6]]]
    sets = [[3, 7], [3], [2, 7]]
    vanishing = []
    for points in sets:
        polynomial = [1]
        for point in points:
            polynomial = mul(polynomial, [-point, 1])
        vanishing.append(polynomial)
    cases = 0
    for x1, x2 in product(range(1, 9), repeat=2):
        combined = [horner(group, x1) for group in groups]
        remainders, quotients = [], []
        for q, points, divisor in zip(combined, sets, vanishing):
            remainder = interpolate_at(points, [evaluate(q, t) for t in points])
            quotient, residue = divide(add(q, scale(remainder, -1)), divisor)
            assert residue == [0]
            # Successive synthetic division obtains the same quotient.
            sequential = q
            for point in points:
                sequential, _ = divide(sequential, [-point, 1])
            assert sequential == quotient
            remainders.append(remainder)
            quotients.append(quotient)
        qprime = horner(quotients, x2)
        for x3 in range(P):
            if any(x3 in points for points in sets):
                continue
            values = [evaluate(q, x3) for q in combined]
            fractions = [(u - evaluate(r, x3)) * pow(evaluate(v, x3), -1, P) % P
                         for u, r, v in zip(values, remainders, vanishing)]
            expected = horner([[v] for v in fractions], x2)[0]
            assert expected == evaluate(qprime, x3)
            final = horner([qprime] + combined, 19)
            claim = horner([[expected]] + [[u] for u in values], 19)[0]
            assert evaluate(final, x3) == claim
            # Change one claimed combined evaluation, leaving commitments fixed.
            wrong = interpolate_at(sets[0], [
                (evaluate(combined[0], t) + int(i == 0)) % P
                for i, t in enumerate(sets[0])])
            bad_fractions = list(fractions)
            bad_fractions[0] = (
                (values[0] - evaluate(wrong, x3))
                * pow(evaluate(vanishing[0], x3), -1, P) % P)
            bad_claim = horner([[v] for v in bad_fractions], x2)[0]
            assert bad_claim != evaluate(qprime, x3)
            cases += 1
    print(f"Multi-opening Horner/interpolation checks: {cases} honest and wrong claims")


def check_lookup_and_rows():
    a, table = [3, 1, 3, 3], [1, 2, 3, 4]
    ap, sp = [1, 3, 3, 3], [1, 3, 2, 4]
    assert sorted(a) == sorted(ap) and sorted(table) == sorted(sp)
    assert ap[0] == sp[0]
    assert all((ap[i] - sp[i]) * (ap[i] - ap[i - 1]) == 0 for i in range(4))
    for beta, gamma in product(range(1, 12), repeat=2):
        accumulator = 1
        for ai, si, api, spi in zip(a, table, ap, sp):
            accumulator = accumulator * (ai + beta) * (si + gamma) % P
            accumulator = accumulator * pow((api + beta) * (spi + gamma), -1, P) % P
        assert accumulator == 1
    assert (15 + (9 - 2) - 1) // (9 - 2) == 3
    assert (9 - 1) * 2048 == 16384
    # Two reserved rows hide two off-domain evaluations, not three.
    domain = [1, 22, 96, 75]
    fixed_factor = mul([-domain[0], 1], [-domain[1], 1])
    query_points = [2, 3]
    observations = set()
    for c0, c1 in product(range(P), repeat=2):
        mask = mul(fixed_factor, [c0, c1])
        observations.add(tuple(evaluate(mask, x) for x in query_points))
    assert len(observations) == P**2
    print("Lookup example, degree/chunk counts and full-rank row masking checked")


if __name__ == "__main__":
    check_ipa()
    check_multiopen()
    check_lookup_and_rows()
    print("All rewritten Halo algebra checks passed")

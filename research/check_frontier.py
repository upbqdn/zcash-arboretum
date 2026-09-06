#!/usr/bin/env python3
"""Arithmetic/state checks for the four clean frontier rewrites.

These are independent small models, not production cryptography or a
verification of network implementation. Run from the repository root:
  python3 -B research/check_frontier.py
"""

from collections import Counter
from fractions import Fraction as F
from itertools import combinations, product
from math import isclose, log
import unittest


def weights(ids, q):
    result = []
    for i in ids:
        value = 1
        for j in ids:
            if i != j:
                value = value * j * pow(j - i, -1, q) % q
        result.append(value)
    return result


def evaluate(coefficients, x, q):
    return sum(a * pow(x, j, q) for j, a in enumerate(coefficients)) % q


def prefix(a, b):
    return b[:len(a)] == a


def compatible(a, b):
    return prefix(a, b) or prefix(b, a)


def truncate(chain, depth):
    return chain[:max(1, len(chain) - depth)]


def common(a, b):
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    return a[:i]


def update(final, chain, snapshot, sigma, mu):
    candidate = common(snapshot, truncate(chain, sigma))
    hazard = not compatible(candidate, final)
    if prefix(final, candidate):
        final = candidate
    confirmed = truncate(chain, mu)
    available = confirmed if prefix(final, confirmed) else final
    return final, available, hazard


def supply_transition(state, burn, issue, finalise=False, cap=2**64 - 1):
    """One-asset accounting projection; caller retains input on rejection."""
    balance, final = state
    if not 0 <= burn <= min(balance, 2**63 - 1):
        raise ValueError("invalid burn")
    balance -= burn
    if issue is not None:
        if final or issue < 0 or balance + issue > cap:
            raise ValueError("invalid issuance")
        balance += issue
        final |= finalise
    return balance, final


class FrontierRewriteChecks(unittest.TestCase):
    def test_flyclient_exact_sample_count(self):
        self.assertLessEqual(F(9, 10)**422, F(1, 2)**64)
        self.assertGreater(F(9, 10)**421, F(1, 2)**64)

    def test_flyclient_tiling_and_density(self):
        for c, k in product((F(1, 4), F(1, 2), F(3, 4)), range(1, 9)):
            delta = c**k
            intervals = [(1 - c**i, 1 - c**(i + 1)) for i in range(k)]
            self.assertEqual(intervals[0][0], 0)
            self.assertEqual(intervals[-1][1], 1 - delta)
            self.assertEqual(sum(b - a for a, b in intervals), 1 - delta)
            for a, b in intervals:
                self.assertEqual(b - a, (1 - c) * (1 - a))
                mass = log(float((1 - a) / (1 - b))) / log(float(1 / delta))
                self.assertTrue(isclose(mass, 1 / k, abs_tol=1e-12))

    def test_frost_worked_signing_and_randomisation(self):
        q, ids = 101, [1, 3, 5]
        lam = weights(ids, q)
        shares = [evaluate([42, 17, 29], i, q) for i in ids]
        self.assertEqual(lam, [65, 24, 13])
        self.assertEqual(shares, [88, 51, 44])
        self.assertEqual(sum(lam) % q, 1)
        self.assertEqual(sum(a * b for a, b in zip(lam, shares)) % q, 42)
        effective = [(d + r * e) % q for d, e, r in
                     zip([11, 13, 17], [19, 23, 29], [2, 4, 6])]
        z = [(r + 7 * l * x) % q for r, l, x in zip(effective, lam, shares)]
        self.assertEqual(effective, [49, 4, 90])
        self.assertEqual(z, [93, 88, 54])
        self.assertEqual(sum(z) % q, 33)
        for alpha in range(q):
            shifted = sum(l * (x + alpha) for l, x in zip(lam, shares)) % q
            self.assertEqual(shifted, (42 + alpha) % q)
            self.assertEqual(sum(l * (-x) for l, x in zip(lam, shares)) % q, -42 % q)

    def test_shamir_private_share_distribution(self):
        q = 7
        distributions = []
        for secret in range(q):
            counts = Counter(tuple(evaluate([secret, a, b], i, q) for i in (1, 3))
                             for a, b in product(range(q), repeat=2))
            self.assertEqual(set(counts.values()), {1})
            distributions.append(counts)
        self.assertTrue(all(d == distributions[0] for d in distributions))

    def test_frost_reused_nonce_equations_recover_share(self):
        q, d, e, share = 101, 11, 19, 88
        rho, beta = [2, 4, 6], [3, 7, 13]
        z = [(d + r * e + b * share) % q for r, b in zip(rho, beta)]
        a, b = rho[1] - rho[0], beta[1] - beta[0]
        c, h = rho[2] - rho[0], beta[2] - beta[0]
        det = (a * h - b * c) % q
        recovered_share = (a * (z[2] - z[0]) - c * (z[1] - z[0])) * pow(det, -1, q) % q
        recovered_e = ((z[1] - z[0]) * h - (z[2] - z[0]) * b) * pow(det, -1, q) % q
        self.assertEqual(recovered_share, share)
        self.assertEqual(recovered_e, e)
        self.assertEqual((z[0] - rho[0] * recovered_e - beta[0] * recovered_share) % q, d)

    def test_zsa_reference_and_encodings(self):
        source = [
            204, 54, 96, 25, 89, 33, 59, 107, 12, 219, 150, 167, 92,
            23, 195, 166, 104, 169, 127, 13, 106, 140, 92, 225, 100,
            165, 24, 234, 155, 169, 165, 14, 167, 81, 145, 253, 134,
            27, 15, 241, 14, 98, 176,
        ]
        encoded = bytes.fromhex(
            "cc36601959213b6b0cdb96a75c17c3a668a97f0d6a"
            "8c5ce164a518ea9ba9a50ea75191fd861b0ff10e62b0")
        self.assertEqual(encoded, bytes(source))
        self.assertEqual(len(encoded), 43)
        self.assertEqual(1 + 33 + 32, 66)
        self.assertEqual(256 + 256 + 64 + 255 + 255 + 256, 1342)
        self.assertLess((2**32 - 1) * (2**64 - 1) + (2**63 - 1), 2**97)

    def test_zsa_curve_generator(self):
        p = 2**256 - 2**32 - 977
        n = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)
        x = int("79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798", 16)
        y = int("483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8", 16)
        self.assertEqual(y * y % p, (x**3 + 7) % p)

        def add(a, b):
            if a is None:
                return b
            if b is None:
                return a
            ax, ay = a
            bx, by = b
            if ax == bx and (ay + by) % p == 0:
                return None
            slope = ((3 * ax * ax) * pow(2 * ay, -1, p) if a == b
                     else (by - ay) * pow(bx - ax, -1, p)) % p
            rx = (slope * slope - ax - bx) % p
            return rx, (slope * (ax - rx) - ay) % p

        total, base, scalar = None, (x, y), n
        while scalar:
            if scalar & 1:
                total = add(total, base)
            base = add(base, base)
            scalar >>= 1
        self.assertIsNone(total)

    def test_zsa_supply_order_finalisation_and_atomicity(self):
        state = (0, False)
        balances = []
        for burn, issue in [(0, 1000), (100, None), (0, 50)]:
            state = supply_transition(state, burn, issue)
            balances.append(state[0])
        self.assertEqual(balances, [1000, 900, 950])
        self.assertEqual(supply_transition((100, False), 10, 10, cap=100), (100, False))
        old = (100, False)
        with self.assertRaises(ValueError):
            supply_transition(old, 0, 1, cap=100)
        self.assertEqual(old, (100, False))
        final = supply_transition(state, 0, 0, finalise=True)
        with self.assertRaises(ValueError):
            supply_transition(final, 0, 1)
        self.assertEqual(supply_transition(final, 10, None), (940, True))

    def test_zsa_native_inequality_gate(self):
        p = 7
        for dx, dy, native in product(range(p), range(p), (0, 1)):
            feasible = any(
                native * dx % p == 0 and native * dy % p == 0 and
                (1 - native) * (dx * ux - 1) * (dy * uy - 1) % p == 0
                for ux, uy in product(range(p), repeat=2))
            self.assertEqual(feasible, bool(native) == (dx == dy == 0))
        for native, value in product((0, 1), (0, 1, 2**64 - 1)):
            self.assertEqual(value + 1 - native == 0, native == 1 and value == 0)

    def test_crosslink_local_example_and_hazard(self):
        chain = tuple(range(9))
        final, available, hazard = update((0,), chain, chain[:6], 2, 2)
        self.assertEqual((final, available, hazard), (chain[:6], chain[:7], False))
        branch = tuple(range(8)) + ("8p", "9p")
        final, available, hazard = update(final, branch, branch[:5], 2, 2)
        self.assertEqual((final, available, hazard), (chain[:6], branch[:8], False))
        branch += ("10p",)
        final, available, hazard = update(final, branch, branch[:8], 2, 2)
        self.assertEqual((final, available, hazard), (branch[:8], branch[:9], False))
        conflict = (0, "other1", "other2", "other3", "other4")
        kept, shown, hazard = update(final, conflict, conflict[:3], 2, 2)
        self.assertEqual((kept, shown, hazard), (final, final, True))

    def test_crosslink_prefix_transfer_lemmas(self):
        chains = [(0,) + bits for size in range(5)
                  for bits in product((1, 2), repeat=size)]
        for a, b in product(chains, repeat=2):
            if compatible(a, b):
                for la, lb in product(range(1, len(a) + 1), range(1, len(b) + 1)):
                    self.assertTrue(compatible(a[:la], b[:lb]))
            for sigma in range(1, 4):
                if prefix(truncate(a, sigma), b):
                    self.assertTrue(compatible(truncate(a, sigma), truncate(b, sigma)))

    def test_crosslink_quorums_and_snapshot_index(self):
        for n in range(1, 101):
            quorum = (2 * n + 2) // 3
            intersection = 2 * quorum - n
            max_faulty = (n - 1) // 3
            self.assertGreater(intersection, max_faulty)
        self.assertEqual((2 * 10 + 2) // 3, 7)
        for sigma, tip in product(range(1, 8), range(10, 15)):
            tail = list(range(tip - sigma + 1, tip + 1))
            self.assertEqual(len(tail), sigma)
            self.assertEqual(tail[0] - 1, tip - sigma)
            self.assertEqual(tip - tail[0], sigma - 1)


if __name__ == "__main__":
    unittest.main()

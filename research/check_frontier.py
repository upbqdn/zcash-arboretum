#!/usr/bin/env python3
"""Independent arithmetic checks for the 2026-09-05 frontier audit.

These small models check explanations and numbers, not production crypto.
Run with: python3 research/check_frontier.py
"""

from fractions import Fraction as F
from itertools import combinations, product
from math import ceil, comb, isclose, log
import unittest


def catch_up(q, n):
    """Exact finite-sum version of the guide's tie-success convention."""
    if q >= F(1, 2):
        return F(1)
    p = 1 - q
    return 1 - sum(comb(n + m - 1, m) *
                   (p**n * q**m - q**n * p**m)
                   for m in range(n + 1))


def evaluate(coefficients, x):
    return sum(a * x**i for i, a in enumerate(coefficients))


class FrontierChecks(unittest.TestCase):
    def test_flyclient_density_and_sample_bound(self):
        for c, k in product((0.25, 0.5, 0.75), range(2, 10)):
            delta = c**k
            integral = lambda a, b: log((1 - b) / (1 - a)) / log(delta)
            self.assertTrue(isclose(integral(0, 1 - delta), 1))
            for i in range(k):
                self.assertTrue(isclose(integral(1 - c**i, 1 - c**(i + 1)),
                                        1 / k))
            m = ceil(50 / (log(1 - 1 / k) / log(0.5)))
            self.assertLessEqual(F(k - 1, k)**m, F(1, 2**50))
            self.assertGreater(F(k - 1, k)**(m - 1), F(1, 2**50))

    def test_shamir_and_additive_share_conversion(self):
        q, secret = 101, 42
        for size in range(3, 6):
            for ids in combinations(range(1, 6), size):
                weights = {}
                for i in ids:
                    weight = 1
                    for j in ids:
                        if j != i:
                            weight = weight * j * pow(j - i, -1, q) % q
                    weights[i] = weight
                shares = {i: evaluate([secret, 17, 29], i) % q for i in ids}
                self.assertEqual(sum(weights[i] * shares[i] for i in ids) % q,
                                 secret)
                converted = {i: i * pow(weights[i], -1, q) % q for i in ids}
                self.assertEqual(sum(weights[i] * converted[i] for i in ids) % q,
                                 sum(ids) % q)

    def test_zsa_proof_sizes_and_x_extraction(self):
        self.assertEqual([2848 + 2272 * n for n in (1, 2)], [5120, 7392])
        self.assertEqual([2720 + 2272 * n for n in (1, 2)], [4992, 7264])
        # On y^2 = x^3 + 2 over F_17, distinct opposite points share x.
        self.assertEqual(6**2 % 17, (0**3 + 2) % 17)
        self.assertEqual(11**2 % 17, (0**3 + 2) % 17)
        self.assertNotEqual(6, 11)

    def test_pq_probability_table(self):
        self.assertEqual(3 * 60 - 254, -74)   # cubic QROM term
        self.assertEqual(2 * 60 - 254, -134)  # quadratic classical comparison
        for f, g in product((F(1, 100), F(1, 20), F(1, 10), F(1, 4)),
                            (1, 2, 10, 100)):
            q = g * f / (g * f + 1 - f)
            self.assertEqual(q > F(1, 2), g > (1 - f) / f)
            for n in (6, 10):
                if q < F(1, 2):
                    # Independent binomial-tail identity.
                    tail = 2 * sum(comb(2 * n - 1, j) * q**j *
                                   (1 - q)**(2 * n - 1 - j)
                                   for j in range(n, 2 * n))
                    self.assertEqual(catch_up(q, n), tail)
        for f, g, n, percent in (
                (F(1, 100), 10, 6, 0.037), (F(1, 100), 10, 10, 0.0004),
                (F(1, 20), 10, 6, 28.0), (F(1, 20), 10, 10, 16.0),
                (F(1, 10), 2, 6, 1.44), (F(1, 10), 2, 10, 0.15),
                (F(1, 4), 2, 6, 49.3), (F(1, 4), 2, 10, 37.2)):
            q = g * f / (g * f + 1 - f)
            self.assertAlmostEqual(float(100 * catch_up(q, n)), percent,
                                   delta=0.05 if percent >= 10 else
                                   0.005 if percent >= 0.1 else 0.0005)

    def test_pq_encoding_thought_experiment(self):
        original = 820 + 64 + 64 + 2720 + 2272
        substitution = 820 - 32 + 1088 + 2 * 2420 + 2720 + 2272
        self.assertEqual(original, 5940)
        self.assertEqual(substitution, 11708)
        self.assertEqual(round(substitution / original, 2), 1.97)
        self.assertEqual(148 - 32 + 1088, 1204)
        self.assertEqual(round(1204 / 148, 1), 8.1)
        self.assertEqual([round(n / 64, 1) for n in (2420, 3309, 7856)],
                         [37.8, 51.7, 122.8])

    def test_tachyon_sequence_identities(self):
        for left, right in product(([], [2], [2, 3]), ([], [5], [5, 7])):
            for x in (0, 1, 2, 17):
                s = len(left)
                lhs, rhs = evaluate(left + [1], x), evaluate(right + [1], x)
                self.assertEqual(evaluate(left + right + [1], x),
                                 lhs + x**s * (rhs - 1))
                self.assertEqual(evaluate(left + [11] + right + [1], x),
                                 lhs + x**s * (11 - 1) + x**(s + 1) * rhs)
        # Nonzero sentinel polynomial can still commit to group identity.
        # In additive Z_101, G0=1 and G1=37, [64]G0 + G1 = 0.
        self.assertEqual((64 + 37) % 101, 0)

    def test_tachyon_epoch_parameters(self):
        self.assertEqual(4**10, 2**20)
        self.assertEqual(2**12, 4096)
        for index in (0, 1, 4095, 4096, 2**20 - 1):
            chunks = [(index // 4**i) % 4 for i in reversed(range(10))]
            self.assertEqual(sum(c * 4**(9 - i) for i, c in enumerate(chunks)),
                             index)

    def test_crosslink_compatibility_headers_rewards(self):
        earlier, later = ('genesis', 'a'), ('genesis',)
        self.assertEqual(earlier[:len(later)], later)  # compatible
        self.assertNotEqual(later[:len(earlier)], earlier)  # not monotone
        tip, sigma = 100, 10
        headers = list(range(tip - sigma + 1, tip + 1))
        self.assertEqual((headers[-1], headers[0], tip - sigma), (100, 91, 90))
        for active_weight in range(101):
            reward, commission = F(1000), F(1, 10)
            paid = (1 - commission) * reward + commission * active_weight / 100 * reward
            self.assertLessEqual(paid, reward)
            self.assertEqual(reward - paid,
                             commission * (100 - active_weight) / 100 * reward)

    def test_voting_quantisation_and_tally_bounds(self):
        d, cap = 12_500_000, 2**24
        self.assertEqual(cap - d, 4_277_216)
        self.assertEqual(F(cap - d, d), F(534_652, 1_562_500))
        for q, r in product((1, 2, 100, 2**30), (0, cap - d - 1, cap - d, d - 1)):
            value = q * d + r
            accepted = [other for other in (q - 2, q - 1, q, q + 1, q + 2)
                        if 1 <= other <= 2**30 and 0 <= value - other * d < cap]
            expected = [q - 1, q] if q >= 2 and r < cap - d else [q]
            self.assertEqual(accepted, expected)
        self.assertLess(2**30 * d, 2**54)
        self.assertEqual(21_000_000 * 10**8 // d, 168_000_000)
        self.assertLess(168_000_000, 2**28)
        self.assertEqual(2**14 * 2**14, 2**28)


if __name__ == '__main__':
    unittest.main(verbosity=2)

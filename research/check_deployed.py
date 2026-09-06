#!/usr/bin/env python3
"""Independent arithmetic and state-machine examples for the fresh drafts.

Toy tree hashes test ordering and rollback, not the production Sinsemilla
implementation. No example here generates or verifies a production proof.
"""

from fractions import Fraction
from hashlib import blake2b
from math import comb


def compact_size(value):
    assert 0 <= value < 2**64
    if value < 253:
        return bytes([value])
    width, prefix = (2, 253) if value <= 65535 else (
        (4, 254) if value <= 2**32 - 1 else (8, 255)
    )
    return bytes([prefix]) + value.to_bytes(width, "little")


def to_compact(target):
    assert target > 0
    size = (target.bit_length() + 7) // 8
    mantissa = target << (8 * (3 - size)) if size <= 3 else (
        target >> (8 * (size - 3))
    )
    if mantissa >= 2**23:
        mantissa >>= 8
        size += 1
    return mantissa + (size << 24)


def to_target(bits):
    size, mantissa = bits >> 24, bits & 0x7FFFFF
    if bits & 0x800000:
        return 0
    return mantissa << (8 * (size - 3)) if size >= 3 else (
        mantissa >> (8 * (3 - size))
    )


def trunc_div(value, divisor):
    return value // divisor if value >= 0 else -((-value) // divisor)


def adjusted_target(mean_target, elapsed, limit):
    expected = 17 * 75
    damped = expected + trunc_div(elapsed - expected, 4)
    bounded = max(expected * 84 // 100,
                  min(expected * 132 // 100, damped))
    return min(limit, (mean_target // expected) * bounded)


def confirmation_probability(q, confirmations):
    """Tie is success; the attack begins level at the payment fork."""
    p = 1 - q
    return 1 - sum(
        Fraction(comb(confirmations + k - 1, k)) * p**confirmations
        * q**k * (1 - (q / p)**(confirmations - k))
        for k in range(confirmations)
    )


def toy_hash(left, right):
    return blake2b(left + right, digest_size=32,
                   person=b"ArboretumToyTree").digest()


def tree_root(leaves, depth=5):
    assert len(leaves) <= 2**depth
    row = list(leaves) + [bytes(32)] * (2**depth - len(leaves))
    while len(row) > 1:
        row = [toy_hash(row[i], row[i + 1]) for i in range(0, len(row), 2)]
    return row[0]


def frontier_append(frontier, count, leaf):
    cursor, level = leaf, 0
    old_count = count
    while count & 1:
        cursor = toy_hash(frontier.pop(level), cursor)
        count >>= 1
        level += 1
    frontier[level] = cursor
    return old_count + 1


def frontier_root(frontier, count, depth=5):
    assert 0 <= count <= 2**depth
    if count == 2**depth:
        return frontier[depth]
    cursor = empty = bytes(32)
    for level in range(depth):
        cursor = toy_hash(frontier[level], cursor) if count >> level & 1 else (
            toy_hash(cursor, empty)
        )
        empty = toy_hash(empty, empty)
    return cursor


def tree_path(leaves, position, depth=5):
    assert 0 <= position < len(leaves) <= 2**depth
    row = list(leaves) + [bytes(32)] * (2**depth - len(leaves))
    path, cursor = [], position
    for _ in range(depth):
        path.append(row[cursor ^ 1])
        row = [toy_hash(row[i], row[i + 1]) for i in range(0, len(row), 2)]
        cursor //= 2
    return path


def path_root(leaf, position, path):
    for level, sibling in enumerate(path):
        leaf = toy_hash(sibling, leaf) if position >> level & 1 else (
            toy_hash(leaf, sibling)
        )
    return leaf


def mmr_positions(count):
    peaks, next_position = [], 0
    for _ in range(count):
        altitude, position = 0, next_position
        next_position += 1
        while peaks and peaks[-1][0] == altitude:
            peaks.pop()
            altitude += 1
            position = next_position
            next_position += 1
        peaks.append((altitude, position))
    return next_position, peaks


def main():
    old, payment, change, fee = 80000, 50000, 20000, 10000
    nets = [old - payment, -change]
    assert nets == [30000, -20000] and sum(nets) == fee
    assert 5000 * max(2, 2) == fee
    assert 1 + 11 + 8 + 32 == 52
    assert 52 + 512 + 16 == 580
    assert 32 + 32 + 16 == 80
    assert 5 * 32 + 580 + 80 == 820
    assert 1 + 32 + 32 + 8 + 32 + 32 == 137
    assert 256 + 256 + 64 + 255 + 255 == 1086
    assert 10 + 255 + 255 == 520
    assert 2720 + 2272 * 2 == 7264
    assert 32 * 32 == 1024
    assert 1 + 2 + 1 + 2 + 1 + 1 + 1 + 1 == 10
    assert 1 + 4 + 4 + 32 + 32 == 73
    assert 32 + 32 + 32 + 52 == 148
    assert 4 + 3 * 32 + 4 + 4 + 32 == 140
    assert 512 * 21 // 8 == 1344
    assert 140 + 3 + 1344 == 1487
    assert (1 + 1 + 43, 1 + 1 + 43 + 16) == (45, 61)
    assert (1 + 1 + 20) + 2 * (1 + 1 + 43) + 16 == 128
    assert [x + 2**31 for x in (32, 133, 9)] == [
        0x80000020, 0x80000085, 0x80000009
    ]
    assert (2**16 - 1) * (2**64 - 1) + 2100000000000000 < 2**81

    # Published orchard-0.15.0/src/test_vectors/zip32.rs, seed 00..1f.
    master = blake2b(bytes(range(32)), digest_size=64,
                     person=b"ZcashIP32Orchard").digest()
    assert master[:32].hex() == (
        "7eee3c1017870990a3dd6891b82f80be8976c1e7dc20d60817a5e88e8b2cd4b8"
    )
    assert master[32:].hex() == (
        "ab8b7a00509ef20e469b5292b61d474b7cffcb1657924cda720250ae40526677"
    )
    child = blake2b(master[32:] + b"\x81" + master[:32]
                    + (2**31 + 1).to_bytes(4, "little"), digest_size=64,
                    person=b"Zcash_ExpandSeed").digest()
    assert child[:32].hex() == (
        "98d703fcb40504c95b3b6ed10ecd50082cff97dfd1dd9aa0913c78f977c962af"
    )
    assert child[32:].hex() == (
        "6a041dfb9cfebee97cb1854fdc481cc04f02c9577aa6f13b2c445b80a9669a22"
    )

    seed = bytes(range(32))
    rho = (7).to_bytes(32, "little")
    calls = [blake2b(seed + bytes([tag]) + rho, digest_size=64,
                     person=b"Zcash_ExpandSeed").digest()
             for tag in (4, 5, 9)]
    assert len(set(calls)) == 3
    for tag in (b"Zcash_ExpandSeed", b"Zcash_OrchardKDF",
                b"Zcash_Orchardock", b"ZcashBlockCommit",
                b"ZcashAuthDatHash"):
        assert len(tag) == 16

    assert [len(compact_size(x)) for x in (0, 252, 253, 65535,
                                          65536, 2**32 - 1, 2**32)] == (
        [1, 1, 3, 3, 5, 5, 9]
    )
    assert (144 + 3, 144 + 3 * 9) == (147, 171)
    assert (208 + 4, 208 + 4 * 9) == (212, 244)
    assert (272 + 5, 272 + 5 * 9) == (277, 317)
    assert mmr_positions(11) == (19, [(3, 14), (1, 17), (0, 18)])

    for target in (1, 255, 256, 32767, 32768, 65535,
                   2**80 + 123456789, 2**243 - 1):
        bits = to_compact(target)
        rounded = to_target(bits)
        assert 0 < rounded <= target
        assert to_compact(rounded) == bits
    assert to_target(0x1F07FFFF) == 0x07FFFF << (8 * 28)
    assert (17 * 75, 1275 * 84 // 100, 1275 * 132 // 100) == (
        1275, 1071, 1683
    )
    assert trunc_div(-1, 4) == 0
    # Consensus uses the upper median for the short, even initial windows.
    assert sorted([10, 2, 5, 8])[4 // 2] == 8
    assert sorted([10, 2, 5])[3 // 2] == 5
    assert adjusted_target(1275000, 1275, 2**256) == 1275000
    assert adjusted_target(1275000, 0, 2**256) == 1071000
    assert adjusted_target(1275000, 10000, 2**256) == 1683000
    assert confirmation_probability(Fraction(1, 10), 1) == Fraction(1, 5)
    assert confirmation_probability(Fraction(1, 10), 6) == Fraction(
        59141216, 10**11
    )

    # The v5 Orchard-only two-Action envelope includes four empty counts,
    # an Action count, conditional bundle fields, and length-prefixed proof.
    proof_size = 2720 + 2272 * 2
    v5_size = (20 + 4 + len(compact_size(2)) + 2 * 820 + 1 + 8 + 32
               + len(compact_size(proof_size)) + proof_size + 2 * 64 + 64)
    assert v5_size == 9165

    leaves = [blake2b(bytes([i]), digest_size=32).digest() for i in range(32)]
    frontier, count = {}, 0
    assert frontier_root(frontier, count) == tree_root([])
    for i, leaf in enumerate(leaves):
        previous_paths = [tree_path(leaves[:i], p) for p in range(i)]
        count = frontier_append(frontier, count, leaf)
        assert count == i + 1
        assert set(frontier) == {j for j in range(6) if count >> j & 1}
        root = frontier_root(frontier, count)
        assert root == tree_root(leaves[:count])
        for p in range(count):
            path = tree_path(leaves[:count], p)
            assert path_root(leaves[p], p, path) == root
            for j, sibling in enumerate(path):
                start = ((p >> j) ^ 1) << j
                interval = leaves[start:min(start + 2**j, count)]
                assert sibling == tree_root(interval, depth=j)
            if p < i:
                changed = [j for j in range(5) if path[j] != previous_paths[p][j]]
                assert changed == [(p ^ i).bit_length() - 1]
    checkpoint = leaves[:11]
    fork_root = tree_root(checkpoint)
    assert tree_root(leaves) != fork_root
    alternative = checkpoint + list(reversed(leaves[11:]))
    assert tree_root(alternative) != tree_root(leaves)
    assert tree_root(alternative[:11]) == fork_root
    assert [11 + i for i in range(2)] == [11, 12]
    print("PASS: payment, sizes, ZIP 32 known vectors, PRF tags, compact integers,")
    print("      targets, difficulty, confirmation probability, MMR, all 32 tree")
    print("      append/root/path transitions, and wallet rollback")
    print("Payment: 80000 = 50000 + 20000 + 10000; Action nets +30000,-20000")
    print("q=0.1,z=6,tie-success probability:",
          float(confirmation_probability(Fraction(1, 10), 6)))


if __name__ == "__main__":
    main()

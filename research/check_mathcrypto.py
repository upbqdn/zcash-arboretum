#!/usr/bin/env python3
"""Exact-arithmetic examples for the clean Math/Crypto drafts.

These checks establish the printed identities, not curve primality, security,
or correctness of a production implementation. Only the standard library is
needed. Run from any directory with Python 3.10 or later.
"""

from collections import Counter
from itertools import product
from hashlib import blake2b, sha256
from pathlib import Path
import re
from math import isqrt


P = 2**254 + 45560315531419706090280762371685220353
Q = 2**254 + 45560315531506369815346746415080538113


def add(left, right, modulus):
    if left is None:
        return right
    if right is None:
        return left
    x, y = left
    u, v = right
    if x == u and (y + v) % modulus == 0:
        return None
    slope = ((3 * x * x * pow(2 * y, -1, modulus)) if left == right
             else (v - y) * pow(u - x, -1, modulus)) % modulus
    out_x = (slope * slope - x - u) % modulus
    return out_x, (slope * (x - out_x) - y) % modulus


def mul(scalar, point, modulus):
    out = None
    while scalar:
        if scalar & 1:
            out = add(out, point, modulus)
        point = add(point, point, modulus)
        scalar >>= 1
    return out


def binary_remainder(a, b):
    while a and a.bit_length() >= b.bit_length():
        a ^= b << (a.bit_length() - b.bit_length())
    return a


def byte_mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        a <<= 1
        if a & 256:
            a ^= 0x11B
        b >>= 1
    return out


def byte_pow(a, exponent):
    out = 1
    while exponent:
        if exponent & 1:
            out = byte_mul(out, a)
        a = byte_mul(a, a)
        exponent >>= 1
    return out


def sqrt_mod(a, p):
    a %= p
    if a == 0:
        return 0
    if pow(a, (p - 1) // 2, p) != 1:
        return None
    odd, two_adicity = p - 1, 0
    while odd % 2 == 0:
        odd //= 2
        two_adicity += 1
    nonsquare = 2
    while pow(nonsquare, (p - 1) // 2, p) != p - 1:
        nonsquare += 1
    x, t = pow(a, (odd + 1) // 2, p), pow(a, odd, p)
    c, m = pow(nonsquare, odd, p), two_adicity
    while t != 1:
        i, power = 1, t * t % p
        while power != 1:
            power = power * power % p
            i += 1
        assert i < m
        b = pow(c, 2 ** (m - i - 1), p)
        x, t, c, m = x * b % p, t * b * b % p, b * b % p, i
    assert x * x % p == a
    return x


def decode_point(encoded, p):
    if len(encoded) != 32:
        return False  # Keep invalid distinct from the identity sentinel None.
    integer = int.from_bytes(encoded, "little")
    x, sign = integer % 2**255, integer >> 255
    if x >= p:
        return False
    if x == sign == 0:
        return None
    y = sqrt_mod(x**3 + 5, p)
    if y is None:
        return False
    if y % 2 != sign:
        y = -y % p
    return x, y


def jacobian_ordinary(left, right, p):
    x1, y1, z1 = left
    x2, y2, z2 = right
    u1, u2 = x1 * z2**2 % p, x2 * z1**2 % p
    s1, s2 = y1 * z2**3 % p, y2 * z1**3 % p
    h, r = (u2 - u1) % p, (s2 - s1) % p
    assert h != 0
    x3 = (r * r - h**3 - 2 * u1 * h * h) % p
    y3 = (r * (u1 * h * h - x3) - s1 * h**3) % p
    z3 = h * z1 * z2 % p
    return x3 * pow(z3, -2, p) % p, y3 * pow(z3, -3, p) % p


def poseidon_parameters():
    def bits(value, width):
        return [(value >> i) & 1 for i in reversed(range(width))]

    state = sum((bits(v, w) for v, w in
                 [(1, 2), (0, 4), (255, 12), (3, 12), (8, 10), (56, 10)]), [])
    state += [1] * 30

    def raw():
        out = 0
        for i in (0, 13, 23, 38, 51, 62):
            out ^= state[i]
        state.pop(0)
        state.append(out)
        return out

    for _ in range(160):
        raw()

    def next_integer():
        out = 0
        for _ in range(255):
            while True:
                first, second = raw(), raw()
                if first:
                    out = 2 * out + second
                    break
        return out

    constants = []
    while len(constants) < 192:
        candidate = next_integer()
        if candidate < P:
            constants.append(candidate)
    while True:
        values = [next_integer() % P for _ in range(6)]
        if len(set(values)) == 6:
            break
    matrix = [pow(x + y, -1, P) for x in values[:3] for y in values[3:]]
    # Independently fingerprinted all 192 RCs and all 9 MDS entries in
    # halo2_poseidon 0.1.0/src/fp.rs, each canonical LE32, in source order.
    encoded = b"".join(x.to_bytes(32, "little") for x in constants + matrix)
    assert sha256(encoded).hexdigest() == (
        "a9a13cf048dcb1fdc90989307b50514fc8454fc53853f704d4a5b395b9b98812")
    return constants, matrix


def poseidon_hash(x, y):
    constants, matrix = poseidon_parameters()
    state = [x, y, 2**65]
    for step in range(64):
        state = [(a + b) % P for a, b in
                 zip(state, constants[3 * step:3 * step + 3])]
        state = [pow(a, 5, P) if step < 4 or step >= 60 or i == 0 else a
                 for i, a in enumerate(state)]
        state = [sum(matrix[3 * i + j] * state[j] for j in range(3)) % P
                 for i in range(3)]
    return state[0]


def curve_add(left, right, p, a):
    if left is None:
        return right
    if right is None:
        return left
    x, y = left
    u, v = right
    if x == u and (y + v) % p == 0:
        return None
    slope = ((3 * x * x + a) * pow(2 * y, -1, p) if left == right
             else (v - y) * pow(u - x, -1, p)) % p
    xx = (slope * slope - x - u) % p
    return xx, (slope * (x - xx) - y) % p


def map_constants():
    # Test the constants actually printed in the authored draft, not a second
    # unchecked copy in this script. This is fixture reading, not file editing.
    directory = Path(__file__).resolve().parent
    source_path = (directory.parent if directory.name == "research" else directory)
    source_path /= "crypto-guide.tex"
    source = source_path.read_text()
    values = [int(v, 16) for v in re.findall(
        r"c_(?:\d|\{\d+\})&=\\mathtt\{([0-9a-f]+)\}", source)]
    assert len(values) == 26
    return values[:13], values[13:]


def swu(u, p, a):
    z, b = p - 13, 1265
    t = z * u * u % p
    denominator = (t * t + t) % p
    x = (-b * pow(a, -1, p) * (1 + pow(denominator, -1, p)) % p
         if denominator else b * pow(z * a, -1, p) % p)
    y = sqrt_mod(x**3 + a * x + b, p)
    if y is None:
        x = t * x % p
        y = sqrt_mod(x**3 + a * x + b, p)
    assert y is not None
    if y % 2 != u % 2:
        y = -y % p
    assert (y * y - x**3 - a * x - b) % p == 0
    return x, y


def group_hash(domain, message, p=P):
    a = int("18354a2eb0ea8c9c49be2d7258370742b74134581a27a59f92bb4b0b657a014b"
            if p == P else
            "267f9b2ee592271a81639c4d96f787739673928c7d01b212c515ad7242eaa6b1", 16)
    constants = map_constants()[0 if p == P else 1]
    dst = domain + b"-" + (b"pallas" if p == P else b"vesta")
    dst += b"_XMD:BLAKE2b_SSWU_RO_"
    assert len(dst) < 256
    dst += bytes([len(dst)])
    b0 = blake2b(bytes(128) + message + bytes([0, 128, 0]) + dst).digest()
    b1 = blake2b(b0 + bytes([1]) + dst).digest()
    b2 = blake2b(bytes(x ^ y for x, y in zip(b0, b1)) + bytes([2]) + dst).digest()
    u0, u1 = int.from_bytes(b1, "big") % p, int.from_bytes(b2, "big") % p
    point = curve_add(swu(u0, p, a), swu(u1, p, a), p, a)
    if point is None:
        return None
    x, y = point
    c = constants
    nx = ((c[0] * x + c[1]) * x + c[2]) * x + c[3]
    dx = x * x + c[4] * x + c[5]
    ny = (((c[6] * x + c[7]) * x + c[8]) * x + c[9]) * y
    dy = ((x + c[10]) * x + c[11]) * x + c[12]
    if dx % p == 0 or dy % p == 0:
        return None
    out = nx * pow(dx, -1, p) % p, ny * pow(dy, -1, p) % p
    assert (out[1]**2 - out[0]**3 - 5) % p == 0
    return out


def check_isogeny_polynomials():
    # Coefficient-wise identity, not a finite sampling of x-coordinates.
    for p, c, a in zip((P, Q), map_constants(), (
            int("18354a2eb0ea8c9c49be2d7258370742b74134581a27a59f92bb4b0b657a014b", 16),
            int("267f9b2ee592271a81639c4d96f787739673928c7d01b212c515ad7242eaa6b1", 16))):
        def pmul(f, g):
            out = [0] * (len(f) + len(g) - 1)
            for i, x in enumerate(f):
                for j, y in enumerate(g):
                    out[i + j] = (out[i + j] + x * y) % p
            return out

        def ppow(f, n):
            out = [1]
            for _ in range(n):
                out = pmul(out, f)
            return out

        nx, dx = c[3::-1], [c[5], c[4], 1]
        ny, dy = c[9:5:-1], [c[12], c[11], c[10], 1]
        left = pmul(pmul(ppow(ny, 2), [1265, a, 0, 1]), ppow(dx, 3))
        right1 = pmul(ppow(nx, 3), ppow(dy, 2))
        right2 = pmul(ppow(dx, 3), ppow(dy, 2))
        for i in range(max(map(len, (left, right1, right2)))):
            at = lambda f: f[i] if i < len(f) else 0
            assert (at(left) - at(right1) - 5 * at(right2)) % p == 0
        swu(0, p, a)  # Explicit exceptional input must yield a curve point.


def aes_sbox(a):
    u = byte_pow(a, 254) if a else 0
    rotate = lambda n: ((u << n) | (u >> (8 - n))) & 255
    return u ^ rotate(1) ^ rotate(2) ^ rotate(3) ^ rotate(4) ^ 0x63


def aes256(key, block):
    assert len(key) == 32 and len(block) == 16
    words = [list(key[i:i + 4]) for i in range(0, 32, 4)]
    rcon = 1
    for i in range(8, 60):
        t = words[-1][:]
        if i % 8 == 0:
            t = [aes_sbox(x) for x in t[1:] + t[:1]]
            t[0] ^= rcon
            rcon = byte_mul(2, rcon)
        elif i % 8 == 4:
            t = [aes_sbox(x) for x in t]
        words.append([x ^ y for x, y in zip(words[i - 8], t)])
    state = list(block)

    def add_key(step):
        key_bytes = sum(words[4 * step:4 * step + 4], [])
        return [x ^ y for x, y in zip(state, key_bytes)]

    state = add_key(0)
    for step in range(1, 15):
        state = [aes_sbox(x) for x in state]
        state = [state[4 * ((c + r) % 4) + r] for c in range(4) for r in range(4)]
        if step != 14:
            output = []
            for c in range(4):
                column = state[4 * c:4 * c + 4]
                for row in range(4):
                    value = 0
                    for j, factor in enumerate((2, 3, 1, 1)):
                        value ^= byte_mul(factor, column[(row + j) % 4])
                    output.append(value)
            state = output
        state = add_key(step)
    return bytes(state)


def ff1_88(key, encoded, inverse=False):
    assert len(encoded) == 11
    bits = [(byte >> j) & 1 for byte in encoded for j in range(8)]
    a = int("".join(map(str, bits[:44])), 2)
    b = int("".join(map(str, bits[44:])), 2)
    prefix = bytes([1, 2, 1, 0, 0, 2, 10, 44]) + (88).to_bytes(4, "big") + bytes(4)
    initial = aes256(key, prefix)
    for i in (reversed(range(10)) if inverse else range(10)):
        right = a if inverse else b
        q = bytes(9) + bytes([i]) + right.to_bytes(6, "big")
        r = aes256(key, bytes(x ^ y for x, y in zip(initial, q)))
        y = int.from_bytes(r[:12], "big")
        a, b = ((b - y) % 2**44, a) if inverse else (b, (a + y) % 2**44)
    bits = f"{a:044b}{b:044b}"
    return bytes(sum(int(bits[8 * j + k]) << k for k in range(8)) for j in range(11))


def f4jumble(message, inverse=False):
    assert 48 <= len(message) <= 4194368
    left_len = min(64, len(message) // 2)
    left, right = message[:left_len], message[left_len:]
    xor = lambda a, b: bytes(x ^ y for x, y in zip(a, b))

    def h(i):
        return blake2b(right, digest_size=left_len,
                       person=b"UA_F4Jumble_H" + bytes([i, 0, 0])).digest()

    def g(i):
        return b"".join(blake2b(left, person=b"UA_F4Jumble_G" + bytes([i])
                               + j.to_bytes(2, "little")).digest()
                        for j in range((len(right) + 63) // 64))[:len(right)]

    if inverse:
        for i in (1, 0):
            left = xor(left, h(i))
            right = xor(right, g(i))
    else:
        for i in (0, 1):
            right = xor(right, g(i))
            left = xor(left, h(i))
    return left + right


def bech32m(hrp, data):
    def polymod(values):
        z = 1
        for value in values:
            b = z >> 25
            z = ((z & 0x1FFFFFF) << 5) ^ value
            for i, g in enumerate((0x3B6A57B2, 0x26508E6D, 0x1EA119FA,
                                    0x3D4233DD, 0x2A1462B3)):
                if (b >> i) & 1:
                    z ^= g
        return z

    values = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    z = polymod(values + data + [0] * 6) ^ 0x2BC830A3
    checksum = [(z >> (5 * i)) & 31 for i in reversed(range(6))]
    assert polymod(values + data + checksum) == 0x2BC830A3
    alphabet = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
    return hrp + "1" + "".join(alphabet[x] for x in data + checksum)


def integer_root(value, exponent):
    low, high = 0, 1 << ((value.bit_length() + exponent - 1) // exponent)
    while high - low > 1:
        middle = (low + high) // 2
        if middle**exponent <= value:
            low = middle
        else:
            high = middle
    return low


def first_primes(count):
    primes = []
    candidate = 2
    while len(primes) < count:
        if all(candidate % p for p in primes if p * p <= candidate):
            primes.append(candidate)
        candidate += 1
    return primes


def sha256_explicit(message):
    mask = 2**32 - 1
    rotate = lambda a, n: ((a >> n) | (a << (32 - n))) & mask
    primes = first_primes(64)
    state = [isqrt(p << 64) & mask for p in primes[:8]]
    constants = [integer_root(p << 96, 3) & mask for p in primes]
    padded = message + b"\x80" + bytes((55 - len(message)) % 64)
    padded += (8 * len(message)).to_bytes(8, "big")
    for offset in range(0, len(padded), 64):
        words = [int.from_bytes(padded[offset + i:offset + i + 4], "big")
                 for i in range(0, 64, 4)]
        for i in range(16, 64):
            x, y = words[i - 15], words[i - 2]
            s0 = rotate(x, 7) ^ rotate(x, 18) ^ (x >> 3)
            s1 = rotate(y, 17) ^ rotate(y, 19) ^ (y >> 10)
            words.append((words[i - 16] + s0 + words[i - 7] + s1) & mask)
        a, b, c, d, e, f, g, h = state
        for word, constant in zip(words, constants):
            s1 = rotate(e, 6) ^ rotate(e, 11) ^ rotate(e, 25)
            ch = (e & f) ^ (~e & g)
            t1 = h + s1 + ch + constant + word
            s0 = rotate(a, 2) ^ rotate(a, 13) ^ rotate(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            a, b, c, d, e, f, g, h = ((t1 + s0 + maj) & mask, a, b, c,
                                      (d + t1) & mask, e, f, g)
        state = [(x + y) & mask for x, y in zip(state, (a, b, c, d, e, f, g, h))]
    return b"".join(word.to_bytes(4, "big") for word in state)


def blake2b_explicit(message, size=64, person=bytes(16)):
    assert 1 <= size <= 64 and len(person) == 16
    mask = 2**64 - 1
    rotate = lambda a, n: ((a >> n) | (a << (64 - n))) & mask
    initial = [isqrt(p << 128) & mask for p in first_primes(8)]
    state = initial[:]
    state[0] ^= 0x01010000 ^ size
    state[6] ^= int.from_bytes(person[:8], "little")
    state[7] ^= int.from_bytes(person[8:], "little")
    rows = ["0123456789abcdef", "ea489fd61c02b753", "b8c052fdae367194",
            "7931dcbe265a40f8", "905724afe1bc683d", "2c6a0b834d75fe19",
            "c51fed4a0763928b", "db7ec13950f4862a", "6fe9b308c2d714a5",
            "a2847615fb9e3cd0"]
    for offset in range(0, max(1, len(message)), 128):
        block = message[offset:offset + 128]
        count = offset + len(block)
        block = block.ljust(128, b"\0")
        words = [int.from_bytes(block[i:i + 8], "little") for i in range(0, 128, 8)]
        work = state + initial[:]
        work[12] ^= count & mask
        work[13] ^= count >> 64
        if offset + 128 >= len(message):
            work[14] ^= mask

        def mix(a, b, c, d, x, y):
            work[a] = (work[a] + work[b] + x) & mask
            work[d] = rotate(work[d] ^ work[a], 32)
            work[c] = (work[c] + work[d]) & mask
            work[b] = rotate(work[b] ^ work[c], 24)
            work[a] = (work[a] + work[b] + y) & mask
            work[d] = rotate(work[d] ^ work[a], 16)
            work[c] = (work[c] + work[d]) & mask
            work[b] = rotate(work[b] ^ work[c], 63)

        indices = ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15),
                   (0, 5, 10, 15), (1, 6, 11, 12), (2, 7, 8, 13), (3, 4, 9, 14))
        for step in range(12):
            sigma = [int(x, 16) for x in rows[step % 10]]
            for i, quadruple in enumerate(indices):
                mix(*quadruple, words[sigma[2 * i]], words[sigma[2 * i + 1]])
        state = [x ^ work[i] ^ work[i + 8] for i, x in enumerate(state)]
    return b"".join(word.to_bytes(8, "little") for word in state)[:size]


def chacha20_block(key, nonce, counter):
    assert len(key) == 32 and len(nonce) == 12 and 0 <= counter < 2**32
    encoded = b"expand 32-byte k" + key + counter.to_bytes(4, "little") + nonce
    initial = [int.from_bytes(encoded[i:i + 4], "little") for i in range(0, 64, 4)]
    work, mask = initial[:], 2**32 - 1
    rotate = lambda a, n: ((a << n) | (a >> (32 - n))) & mask

    def quarter(a, b, c, d):
        for first, second in ((16, 12), (8, 7)):
            work[a] = (work[a] + work[b]) & mask
            work[d] = rotate(work[d] ^ work[a], first)
            work[c] = (work[c] + work[d]) & mask
            work[b] = rotate(work[b] ^ work[c], second)

    for _ in range(10):
        for indices in ((0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15),
                        (0, 5, 10, 15), (1, 6, 11, 12), (2, 7, 8, 13), (3, 4, 9, 14)):
            quarter(*indices)
    return b"".join(((x + y) & mask).to_bytes(4, "little") for x, y in zip(initial, work))


def poly1305(key, message):
    assert len(key) == 32
    r = int.from_bytes(key[:16], "little") & 0x0FFFFFFC0FFFFFFC0FFFFFFC0FFFFFFF
    s = int.from_bytes(key[16:], "little")
    accumulator = 0
    for offset in range(0, len(message), 16):
        value = int.from_bytes(message[offset:offset + 16] + b"\x01", "little")
        accumulator = (accumulator + value) * r % (2**130 - 5)
    return ((accumulator + s) % 2**128).to_bytes(16, "little")


def check_hash_and_cipher_vectors():
    for length in (0, 1, 55, 56, 63, 64, 65, 127, 128, 129, 256):
        message = bytes(i % 256 for i in range(length))
        assert sha256_explicit(message) == sha256(message).digest()
        for size in (1, 32, 64):
            for person in (bytes(16), b"Zcash_ExpandSeed"):
                assert blake2b_explicit(message, size, person) == blake2b(
                    message, digest_size=size, person=person).digest()
    assert poseidon_hash(0, 1).to_bytes(32, "little").hex() == (
        "8358d711a0329d38becd54fba7c283ed3e089a39c91b6a9d10efb02bc3f12f06")
    # RFC 8439 sections 2.3.2, 2.5.2 and 2.8.2.
    block = chacha20_block(bytes(range(32)), bytes.fromhex("000000090000004a00000000"), 1)
    assert block.hex() == (
        "10f1e7e4d13b5915500fdd1fa32071c4c7d1f4c733c068030422aa9ac3d46c4e"
        "d2826446079faa0914c2d705d98b02a2b5129cd1de164eb9cbd083e8a2503c4e")
    key = bytes.fromhex("85d6be7857556d337f4452fe42d506a80103808afb0db2fd4abff6af4149f51b")
    assert poly1305(key, b"Cryptographic Forum Research Group").hex() == (
        "a8061dc1305136c6c22b8baf0c0127a9")
    key = bytes(range(0x80, 0xA0))
    nonce = bytes.fromhex("070000004041424344454647")
    associated = bytes.fromhex("50515253c0c1c2c3c4c5c6c7")
    plain = (b"Ladies and Gentlemen of the class of '99: If I could offer you "
             b"only one tip for the future, sunscreen would be it.")
    stream = b"".join(chacha20_block(key, nonce, i + 1)
                      for i in range((len(plain) + 63) // 64))
    cipher = bytes(x ^ y for x, y in zip(plain, stream))
    authenticated = associated + bytes(-len(associated) % 16)
    authenticated += cipher + bytes(-len(cipher) % 16)
    authenticated += len(associated).to_bytes(8, "little") + len(cipher).to_bytes(8, "little")
    assert poly1305(chacha20_block(key, nonce, 0)[:32], authenticated).hex() == (
        "1ae10b594f09e26a7e902ecbd0600691")
    print("Crypto: explicit SHA256/BLAKE2b edge blocks agree with hashlib; Poseidon hash vector pass")
    print("Crypto: RFC ChaCha block, Poly1305 tag and full AEAD tag vectors pass")


def crypto_checks():
    poseidon_parameters()
    check_isogeny_polynomials()
    # Published pasta_curves 0.5.2 test coordinates are Jacobian, so compare
    # their affine interpretations to the independently implemented map.
    for p, message, coords in (
        (P, b"Trans rights now!", (
            "36a6e3a9c50b7b6540cb002c977c82f37f8a875fb51eb35327ee1452e6ce7947",
            "01da3b4403d73252f2d7e9c19bc23dc6a080f2d02f8262fca4f7e3d756ac6a7c",
            "1d48103df8fcbb70d1809c1806c95651dd884a559fec0549658537ce9d94bed9")),
        (Q, b"hello", (
            "12763505036e0e1a6684b7a7d8d5afb7378cc2b191a95e34f44824a06fcbd08e",
            "0256eafc0188b79bfa7c4b2b393893ddc298e90da500fa4a9aee17c2ea4240e6",
            "1b58d4aa4d68c3f4d9916b77c79ff9911597a27f2ee46244e98eb9615172d2ad"))):
        x, y, z = map(lambda s: int(s, 16), coords)
        assert group_hash(b"z.cash:test", message, p) == (
            x * pow(z, -2, p) % p, y * pow(z, -3, p) % p)
    assert group_hash(b"z.cash:Orchard-gd", b"") is not None
    assert len({aes_sbox(a) for a in range(256)}) == 256
    assert aes_sbox(0x53) == 0xED and aes_sbox(0) == 0x63
    for a in range(256):
        v = aes_sbox(a)
        rot = lambda j: ((v << j) | (v >> (8 - j))) & 255
        u = rot(1) ^ rot(3) ^ rot(6) ^ 0x05
        assert (byte_pow(u, 254) if u else 0) == a
    forward = (2, 3, 1, 1)
    inverse = (0x0E, 0x0B, 0x0D, 9)
    for i, j in product(range(4), repeat=2):
        value = 0
        for k in range(4):
            value ^= byte_mul(forward[(k - i) % 4], inverse[(j - k) % 4])
        assert value == int(i == j)
    # FIPS 197 AES-256 example: distinct sequential key and plaintext bytes.
    encrypted = aes256(bytes(range(32)), bytes.fromhex("00112233445566778899aabbccddeeff"))
    assert encrypted.hex() == "8ea2b7ca516745bfeafc49904b496089"
    for key in (bytes(32), bytes(range(32))):
        for index in (0, 1, 2**44 - 1, 2**44, 2**88 - 1):
            message = index.to_bytes(11, "little")
            assert ff1_88(key, ff1_88(key, message), inverse=True) == message
    # Independent f4jumble 0.1.1 documentation vector.
    message = b"The package from Alice arrives tomorrow morning."
    out = f4jumble(message)
    assert out.hex() == ("861c51ee746b0313476967a3483e7e1ff77a2952a17d3ed9"
                         "e0ab0f502e1179430322da9967b613545b1c36353046ca27")
    assert f4jumble(out, inverse=True) == message
    for length in (48, 49, 127, 128, 129, 256, 513):
        message = bytes(i % 256 for i in range(length))
        assert f4jumble(f4jumble(message), inverse=True) == message
    assert bech32m("a", []) == "a1lqfn3a"
    print("Crypto: all 192 Poseidon constants and 9 MDS entries match primary fingerprint")
    print("Crypto: Pallas/Vesta map polynomial identities and independent hash vectors pass")
    print("Crypto: fallback nonidentity, AES S-box/inverse matrices and FIPS vector pass")
    print("Crypto: FF1-88 inverse cases, independent F4Jumble vector, Bech32m vector pass")


def main():
    assert pow(17, -1, 97) == 40
    assert (80 + 80 - 63) % 97 == 0
    counts = Counter(x % 7 for x in range(32))
    assert [counts[x] for x in range(7)] == [5, 5, 5, 5, 4, 4, 4]
    assert sum(abs(7 * counts[x] - 32) for x in range(7)) == 24
    masks = Counter(((u + v) % 5, (u + 2 * v) % 5)
                    for u, v in product(range(5), repeat=2))
    assert len(masks) == 25 and set(masks.values()) == {1}
    masks_bad = Counter(((u + v) % 5, (2 * u + 2 * v) % 5)
                        for u, v in product(range(5), repeat=2))
    assert len(masks_bad) == 5 and set(masks_bad.values()) == {5}
    domain = [pow(22, i, 97) for i in range(4)]
    assert domain == [1, 22, 96, 75]
    coefficients = [3, 5, 7, 11]
    values = [sum(c * pow(x, i, 97) for i, c in enumerate(coefficients))
              % 97 for x in domain]
    assert values == [26, 58, 91, 31]
    recovered = [sum(value * pow(22, (-i * j) % 4, 97)
                     for j, value in enumerate(values)) * pow(4, -1, 97)
                 % 97 for i in range(4)]
    assert recovered == coefficients
    points = [(x, y) for x, y in product(range(19), repeat=2)
              if (y * y - x**3 - 5) % 19 == 0]
    assert len(points) + 1 == 27
    toy = (0, 9)
    assert add(toy, toy, 19) == (0, 10)
    assert mul(3, toy, 19) is None
    for left, right in product(points, repeat=2):
        if left[0] != right[0]:
            scaled_left = (left[0] * 4 % 19, left[1] * 8 % 19, 2)
            scaled_right = (right[0] * 9 % 19, right[1] * 27 % 19, 3)
            assert jacobian_ordinary(scaled_left, scaled_right, 19) == add(
                left, right, 19)
    for modulus in (5, 7, 13, 19, 97):
        squares = {x * x % modulus for x in range(modulus)}
        for value in range(modulus):
            root = sqrt_mod(value, modulus)
            assert (root is not None) == (value in squares)
    assert hex(P) == "0x40000000000000000000000000000000224698fc094cf91b992d30ed00000001"
    assert hex(Q) == "0x40000000000000000000000000000000224698fc0994a8dd8c46eb2100000001"
    for base, order in [(P, Q), (Q, P)]:
        assert (base - 1) % 2**32 == 0
        assert ((base - 1) // 2**32) % 2 == 1
        assert pow(base - 13, (base - 1) // 2, base) == base - 1
        assert pow(5, (base - 1) // 2, base) == base - 1
        assert mul(order, (base - 1, 2), base) is None
        assert decode_point(bytes(32), base) is None
        assert decode_point((2**255).to_bytes(32, "little"), base) is False
        assert decode_point(base.to_bytes(32, "little"), base) is False
        assert decode_point((base - 1).to_bytes(32, "little"), base) == (base - 1, 2)
        negative = ((base - 1) + 2**255).to_bytes(32, "little")
        assert decode_point(negative, base) == (base - 1, base - 2)
    assert Q - P == 86663725065984043395317760
    assert byte_mul(0x57, 0x83) == 0xC1
    assert byte_pow(0x53, 254) == 0xCA
    # A reducible degree-eight polynomial has a monic factor of degree <= 4.
    for degree in range(1, 5):
        for lower_bits in range(1 << degree):
            assert binary_remainder(0x11B, (1 << degree) | lower_bits)
    assert all(byte_mul(a, byte_pow(a, 254)) == 1 for a in range(1, 256))
    print("Math: inversion 17^-1 = 40 mod 97; wraparound 80+80=63 mod 97")
    print("Math: reduction mod 7 counts [5,5,5,5,4,4,4]; distance 3/56")
    print("Math: rank-two masks 25 equally likely pairs; rank-one masks 5")
    print("Math: F97 FFT [3,5,7,11] ->", values)
    print("Math: y^2=x^3+5 over F19 has 27 points; (0,9) has order 3")
    print("Math: Pasta published moduli, two-adicity, nonsquare and [r]G pass")
    print("Math: square-root cases, Jacobian additions and Pasta decoding pass")
    print("Math: AES 57*83=c1; inverse(53)=ca; byte modulus irreducible")


if __name__ == "__main__":
    main()
    crypto_checks()
    check_hash_and_cipher_vectors()

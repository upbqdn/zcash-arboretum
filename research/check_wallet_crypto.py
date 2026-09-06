#!/usr/bin/env python3
"""Independent primary-vector and decoding checks for Crypto section 8.

Run with Python 3.10+, without -O; no dependencies, downloads or upstream
checkout are needed. Reuse the reviewed arithmetic implementations in the
sibling check_mathcrypto module instead of retaining duplicate AES/FF1/F4
implementations. The decoder below directly implements the prose's checks.
These are executable consistency checks, not a security proof or a production
wallet/parser. In particular, the UA checks do not validate receiver curves.

Primary vector provenance:
* NIST SP 800-38A, F.1.5, four AES-256 ECB blocks:
  https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38a.pdf
* orchard 0.15.0, commit 8995ee7e26f8b654a5457d05c95ee5b3132b3edd,
  src/test_vectors/keys.rs (first dk/default_d), src/keys.rs (FF1 bit order).
  The vector producer's default_d is diversifier(0):
  https://github.com/zcash/zcash-test-vectors/blob/master/zcash_test_vectors/orchard/key_components.py
* librustzcash e30517e4335b4d850d35549f8366ba8bf817b17d:
  components/f4jumble/src/{test_vectors.rs,test_vectors_long.rs,lib.rs};
  components/zcash_address/src/kind/unified/address/test_vectors.rs.
  The long F4 vector input is bytes(i mod 256), as specified in lib.rs.
* https://bips.dev/350/ (all seven generic valid and fourteen invalid strings).
  All sources inspected 2026-09-06. Vector bytes are embedded, not read from
  a potentially different version of a local checkout at runtime.
"""

from hashlib import blake2b

from check_mathcrypto import aes256, bech32m, f4jumble, ff1_88


ALPHABET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def decode_symbols(text, *, long_form=False):
    """Generic Bech32m symbols; byte-payload padding is a separate layer."""
    if not long_form and len(text) > 90:
        raise ValueError("generic length limit")
    if any(not 33 <= ord(c) <= 126 for c in text):
        raise ValueError("non-printable ASCII")
    if text.lower() != text and text.upper() != text:
        raise ValueError("mixed letter case")
    text = text.lower()
    separator = text.rfind("1")
    if not 1 <= separator <= 83:
        raise ValueError("missing separator or invalid HRP length")
    hrp, encoded = text[:separator], text[separator + 1:]
    if len(encoded) < 6 or any(c not in ALPHABET for c in encoded):
        raise ValueError("short checksum or invalid data alphabet")
    data = [ALPHABET.index(c) for c in encoded]
    values = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    z = 1
    for value in values + data:
        top = z >> 25
        z = ((z % 2**25) * 32) ^ value
        for i, generator in enumerate((0x3B6A57B2, 0x26508E6D, 0x1EA119FA,
                                        0x3D4233DD, 0x2A1462B3)):
            if top & (1 << i):
                z ^= generator
    if z != 0x2BC830A3:
        raise ValueError("wrong Bech32m checksum")
    return hrp, data[:-6]


def to_symbols(payload):
    bits = "".join(f"{byte:08b}" for byte in payload)
    bits += "0" * (-len(bits) % 5)
    return [int(bits[i:i + 5], 2) for i in range(0, len(bits), 5)]


def from_symbols(symbols):
    if any(not 0 <= symbol < 32 for symbol in symbols):
        raise ValueError("symbol out of range")
    bits = "".join(f"{symbol:05b}" for symbol in symbols)
    whole = len(bits) // 8 * 8
    leftover = bits[whole:]
    if len(leftover) >= 5 or "1" in leftover:
        raise ValueError("non-canonical byte padding")
    return bytes(int(bits[i:i + 8], 2) for i in range(0, whole, 8))


def decode_bytes(text, *, long_form=False):
    hrp, symbols = decode_symbols(text, long_form=long_form)
    return hrp, from_symbols(symbols)


def rejected(call, exception=ValueError):
    try:
        call()
    except exception:
        return
    raise AssertionError("malformed input was accepted")


def aes_ff1_checks():
    key = bytes.fromhex("603deb1015ca71be2b73aef0857d7781"
                        "1f352c073b6108d72d9810a30914dff4")
    for plain, cipher in (
        ("6bc1bee22e409f96e93d7e117393172a", "f3eed1bdb5d2a03c064b5a7e3db181f8"),
        ("ae2d8a571e03ac9c9eb76fac45af8e51", "591ccb10d410ed26dc5ba74a31362870"),
        ("30c81c46a35ce411e5fbc1191a0a52ef", "b6ed21b99ca6f4f9f153e7b1beafed1d"),
        ("f69f2445df4f9b17ad2b417be66c3710", "23304b7a39f9f3ff067d8d8f9e24ecc7"),
    ):
        assert aes256(key, bytes.fromhex(plain)).hex() == cipher
    dk = bytes.fromhex("31d6a685be570f9faf3ca8b052e887840"
                       "b2c9f8d67224ca82aefb9e2ee5bedaf")
    diversifier = bytes.fromhex("8ff3386971cb64b8e77899")
    assert ff1_88(dk, bytes(11)) == diversifier
    assert ff1_88(dk, diversifier, inverse=True) == bytes(11)
    indices = (0, 1, 2**44 - 1, 2**44, 2**88 - 1, 0x123456789ABCDEF0123456)
    outputs = [ff1_88(dk, j.to_bytes(11, "little")) for j in indices]
    assert len(set(outputs)) == len(indices)
    for index, output in zip(indices, outputs):
        assert ff1_88(dk, output, inverse=True) == index.to_bytes(11, "little")
    print("Wallet crypto: 4 NIST AES-256 blocks and pinned Orchard FF1 vector pass")


def jumble_checks():
    for plain, mixed in (
        ("5d7a8f739a2d9e945b0ce152a8049e294c4d6e66b164939daffa2ef6ee692148"
         "1cdd86b3cc4318d9614fc820905d042b",
         "0304d029141b995da5387c125970673504d6c764d91ea6c082123770c7139ccd"
         "88ee27368cd0c0921a0444c8e5858d22"),
        ("b1ef9ca3f24988c7b3534201cfb1cd8dbf69b8250c18ef41294ca97993db546c"
         "1fe01f7e9c8e36d6a5e29d4e30a73594bf5098421c69378af1e40f64e125946f",
         "5271fa3321f3adbcfb075196883d542b438ec6339176537daf859841fe6a5622"
         "2bff76d1662b5509a9e1079e446eeedd2e683c31aae3ee1851d7954328526be1"),
    ):
        plain, mixed = bytes.fromhex(plain), bytes.fromhex(mixed)
        assert f4jumble(plain) == mixed
        assert f4jumble(mixed, inverse=True) == plain
    # Largest valid input reaches block index 65535 in both G rounds.
    length = 4194368
    plain = (bytes(range(256)) * ((length + 255) // 256))[:length]
    mixed = f4jumble(plain)
    assert blake2b(mixed).hexdigest() == (
        "a5f18f163e598d4adb6ea7248057e24c1b61f29b33b7abcdabd420a0f2ee6c3e"
        "d31394652f28b59c44d3ea9ecf85f4d501e6aac14df288efd62cf80d1829d025")
    assert f4jumble(mixed, inverse=True) == plain
    for length in (0, 47, 4194369):
        rejected(lambda: f4jumble(bytes(length)), AssertionError)
    print("Wallet crypto: 2 short F4 vectors, maximum-length vector/inverse, bounds pass")


def text_checks():
    valid = (
        "A1LQFN3A",
        "a1lqfn3a",
        "an83characterlonghumanreadablepartthatcontainsthetheexcludedcharactersbioandnumber11sg7hg6",
        "abcdef1l7aum6echk45nj3s0wdvt2fg8x9yrzpqzd3ryx",
        "11" + "l" * 83 + "udsr8",
        "split1checkupstagehandshakeupstreamerranterredcaperredlc445v",
        "?1v759aa",
    )
    for text in valid:
        hrp, data = decode_symbols(text)
        assert bech32m(hrp, data) == text.lower()
    invalid = (
        "\x201xj0phk", "\x7f1g6xzxy", "\x801vctc34",
        "an84characterslonghumanreadablepartthatcontainsthetheexcludedcharactersbioandnumber11d6pts4",
        "qyrz8wqd2c9m", "1qyrz8wqd2c9m", "y1b0jsk6g", "lt1igcx5c0",
        "in1muywd", "mm1crxm3i", "au1s5cgom", "M1VUXWEZ", "16plkw9", "1p2gdwpf",
    )
    for text in invalid:
        rejected(lambda: decode_symbols(text))
    rejected(lambda: decode_symbols("a1LQFN3A"))
    rejected(lambda: decode_symbols("A12UEL5L"))  # Older Bech32 constant 1.
    rejected(lambda: decode_symbols(bech32m("h" * 84, []), long_form=True))
    # Valid checksums must not override canonical byte-conversion rules.
    for symbols in ([0], [0, 1], [0, 0, 0]):
        text = bech32m("u", symbols)
        assert decode_symbols(text) == ("u", symbols)
        rejected(lambda: decode_bytes(text))
    assert decode_bytes(bech32m("u", [0, 0])) == ("u", b"\0")
    for length in range(65):
        payload = bytes(range(length))
        text = bech32m("u", to_symbols(payload))
        assert decode_bytes(text, long_form=True) == ("u", payload)
        if len(text) > 90:
            rejected(lambda: decode_bytes(text))
    for byte in range(256):
        payload = bytes([byte])
        assert from_symbols(to_symbols(payload)) == payload
    # All single substitutions of a checksum symbol in this published vector.
    for position in range(2, 8):
        for character in ALPHABET:
            if character != "a1lqfn3a"[position]:
                changed = "a1lqfn3a"[:position] + character + "a1lqfn3a"[position + 1:]
                rejected(lambda: decode_symbols(changed))
    print("Wallet crypto: all 7/14 BIP350 vectors, case, length and padding checks pass")


def unified_address_checks():
    # Revision-0 vectors 1 and 4: all lengths/typecodes here fit one-byte
    # CompactSize. This checks serialization/composition, not a general parser.
    vectors = (
        (((0, "7bb83570b8fae146e03c5331a020b1e0892f631d"),
          (2, "d8ef8293d26de832e7193f296ba1922d90f122c6135bc231eebd91efdb03b1a8"
              "606771cd4fd6480574d43e")),
         "u1l8xunezsvhq8fgzfl7404m450nwnd76zshscn6nfys7vyz2ywyh4cc5daaq0c7q2"
         "su5lqfh23sp7fkf3kt27ve5948mzpfdvckzaect2jtte308mkwlycj2u0eac077wu70vqcetkxf"),
        (((0, "cad268758c5e71493066446b98e71df9d1d6a5ca"),
          (2, "9f6e0bf90a18fc0b9b83ae9f23ad4358648638482b5def8975635b66fd8a7083"
              "35f9235a3186ec0f033f84"),
          (3, "cecbe5e689a453a3fe10ccf7617e6c1fb382819d7fc9200a1f42092ac84a3037"
              "8f8c1fb90dff71a6d5042d")),
         "u1pg2aaph7jp8rpf6yhsza25722sg5fcn3vaca6ze27hqjw7jvvhhuxkpcg0ge9xh6"
         "drsgdkda8qjq5chpehkcpxf87rnjryjqwymdheptpvnljqqrjqzjwkc2ma6hcq666kgw"
         "fytxwac8eyex6ndgr6ezte66706e3vaqrd25dzvzkc69kw0jgywtd0cmq52q5lkw6uh7hyvzjse8ksx"),
    )
    for items, expected in vectors:
        payload = b"".join(bytes([kind, len(bytes.fromhex(value))]) + bytes.fromhex(value)
                           for kind, value in items)
        padded = payload + b"u" + bytes(15)
        jumbled = f4jumble(padded)
        assert bech32m("u", to_symbols(jumbled)) == expected
        assert len(expected) > 90
        rejected(lambda: decode_bytes(expected))
        hrp, decoded = decode_bytes(expected, long_form=True)
        assert hrp == "u" and decoded == jumbled
        assert f4jumble(decoded, inverse=True) == payload + hrp.encode() + bytes(15)
        assert decode_bytes(expected.upper(), long_form=True) == (hrp, decoded)
    print("Wallet crypto: 2 pinned Unified Address vectors match byte-for-byte, including Orchard")


if __name__ == "__main__":
    aes_ff1_checks()
    jumble_checks()
    text_checks()
    unified_address_checks()

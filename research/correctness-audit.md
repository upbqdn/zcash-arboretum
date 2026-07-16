# Correctness audit — guide-fix worklist

Wave-0, 2026-07-16.

## Method

A model-diff pass: each guide's factual claims were diffed against ground truth
(zcash/zips `69610984`, protocol.tex `662dc87`; orchard HEAD `bef8a27`;
librustzcash `e30517e4`; zebra-crosslink `6d02a1b`; tfl-book `fe6e1d6f`;
voting-circuits `4c39abd`, vote-sdk `cb915f5`; RFC 9591; ePrint 2024/436). Each
divergence is sorted into one of two bins:

- **guide-fix** — the guide is wrong; correct the guide. Tracked here.
- **upstream defect** — the guide is right, the upstream source is wrong.
  Tracked in `upstream-defects.md`.

This file is the guide-fix bin only. Findings are firsthand-cited but this wave
is breadth-first (a shallow diff, not a per-volume grid), so absence of a finding
in a volume is not evidence of correctness there.

## This wave's coverage

Volumes touched: Ironwood, ZSA, Wallet, Crosslink, FROST, Voting.
Bin totals: **3 guide-fixes** (1 medium, 2 low), 11 upstream defects (2 medium,
9 low — see the other file).

All three guide-fixes are localized citation/scope errors, not structural
rewrites; the guide reasoning is sound in each case and the surrounding text
already states the correct fact, so these are one- to three-line edits.

## Priority worklist

| # | Sev | Volume : section | Area |
|---|-----|------------------|------|
| G1 | medium | Ironwood : `sec:action-stmt` (Def A8/A9) | `enableSpends` rule for `flagsIronwood` phrased as universal, not coinbase-only |
| G2 | low | Ironwood : `sec:action-stmt` (`rem:action-versions`) | `crate orchard 0.15.0` version pin — no such release exists |
| G3 | low | ZSA : `sec:zsa-v6` (Action Groups) | ZIP-230 `nAGExpiryHeight` MUST mis-attributed to the rationale section |

---

### G1 — `enableSpends` consensus rule for `flagsIronwood` reads as universal (medium)

**Volume : section.** Ironwood Guide, `sec:action-stmt`, Definition "Orchard
Action statement" A8/A9 — `ironwood-guide.tex:1512-1514`.

**What's wrong.** The clause "and from NU6.3 the `enableSpends` bit of
`flagsIronwood` MUST be 0 --- ZIP-229" has its own subject and a temporal
("from NU6.3") rather than coinbase scope, so it asserts a *universal* NU6.3
rule. ZIP-229 forces `enableSpends = 0` on `flagsIronwood` only **for coinbase
transactions** (`zip-0229.md:256-257`); ZIP-258's NU6.3 universal consensus list
(`zip-0258.md:88-99`) carries no such blanket rule — only coinbase-empty-Orchard,
`enableCrossAddress = 0`, and `valueBalanceOrchard >= 0`. Read literally the
guide forbids ever spending an Ironwood note, inverting the purpose of the pool
value flows into. Contradicted directly by `protocol.tex:13574` (permits
`nActionsIronwood > 0` with `enableSpendsIronwood = 1`) and
`protocol.tex:13579-13580` ("at least one of `enableSpendsIronwood` and
`enableOutputsIronwood` MUST be 1" from NU6.3).

**The fix.** Re-scope the second clause to coinbase, or drop it. Correct
statement: coinbase must set `enableSpendsIronwood = 0` (the v5
`enableSpendsOrchard = 0` analog, `protocol.tex:13654`); non-coinbase Ironwood
actions may set `enableSpends = 1`. If a universal NU6.3 line is wanted, cite the
real ones from `zip-0258.md:88-99`.

---

### G2 — `crate orchard 0.15.0` version pin does not exist (low)

**Volume : section.** Ironwood Guide, `sec:action-stmt`, Remark
`rem:action-versions` — `ironwood-guide.tex:1535`; recurs at `:1986` and `:2472`.

**What's wrong.** Body text pins the Ironwood circuit source to "crate `orchard`
0.15.0 `src/circuit.rs`", but the Ironwood code is unreleased dev on 0.14.0.
orchard HEAD `bef8a27` (`git describe` = `0.14.0-18-gbef8a27`): `Cargo.toml:3`
`version = "0.14.0"`, no `0.15.0` tag and no `0.15.0` string anywhere;
`CHANGELOG.md` top section is `[Unreleased]` and its body is exactly the Ironwood
circuit / `enableCrossAddress` work. The cited symbol names are all correct
(`supports_cross_address_restriction` at `circuit.rs:147`; the
`InsecurePreNu6_2` / `FixedPostNu6_2` / `PostNu6_3` enum) — only the version
number is wrong. The guide contradicts itself: its own methodology note at
`ironwood-guide.tex:2470-2473` pins "crate orchard at git commit `bef8a27e`
(v0.14.0, 2026-06-16)" for the same circuit claims.

**The fix.** Replace "0.15.0" with the pin the methodology note already uses —
orchard git `bef8a27` (0.14.0 + unreleased Ironwood) — at `:1535`, `:1986`, and
`:2472`. A phrasing like "crate `orchard`, unreleased @ `bef8a27` (`src/circuit.rs`)"
removes the forward-looking guess and matches `:2470-2473`.

---

### G3 — ZIP-230 `nAGExpiryHeight` MUST mis-attributed to the rationale section (low)

**Volume : section.** ZSA Guide, `sec:zsa-v6` (Orchard fields: Action Groups) —
`zsa-guide.tex:2955-2957`.

**What's wrong.** After citing "(ZIP-230, Rationale for `nAGExpiryHeight`)", the
guide writes "The same rationale section states ``In NU7, `nExpiryHeight` MUST be
set to 0''", attributing the sentence to the rationale section. The sentence is
verbatim in ZIP-230 (`zip-0230.rst:321-322`) but lives in the **normative MUST
bullet list** that *precedes* the rationale heading (heading at `zip-0230.rst:324`);
the rationale body (`:327-329`) only introduces `nAGExpiryHeight` for ZIP-228
forward compatibility and draws a ZIP-203 analogy — it never contains the "In NU7
... MUST be set to 0" sentence (grep confirms the sentence occurs once, at line
321). The mis-attribution also demotes a normative MUST to non-normative
rationale prose.

**The fix.** Attribute the sentence to ZIP-230's normative consensus-rule bullet
list (`zip-0230.rst:315-322`), not "Rationale for `nAGExpiryHeight`", and label
it normative. Keep the separate, correct citation of the rationale section for
the `nAGExpiryHeight = 0`-by-consensus convention.

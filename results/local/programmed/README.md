# wspnet/programmed: a hand-written classical evaluation inside SFNNv20 nets

Every weight in these nets was written by hand from chess knowledge, through closed-form integer formulas.
Nothing was fitted to data, and no gradient, optimiser or training of any kind was used. All compute ran on
this Mac: the engine is the local Stockfish master build 8833740, and the games used local fastchess.

| net | content | FT slots used (of 512) | exactness (3,009 positions) | smoke result, 200 games at 10+0.1 |
|---|---|---|---|---|
| `out/v1.nnue` | PeSTO material + piece-square tables, fixed (mg+eg)/2 | 123 | PASS, engine == simulate 3009/3009; abs(engine − ideal) ≤ 1.0 | vs material-only net (infra): **+511.5 ± 95** (184 W, 4 L, 12 D) |
| `out/v2.nnue` | v1, but tapered mg↔eg by exact game phase, computed by the pair product | 167 | PASS, 3009/3009; mean abs(engine − ideal) 5.0, max 36.9 | vs v1: **+107.5 ± 35** (96 W, 36 L, 68 D) |
| `out/v3.nnue` | v2 + threats, side-to-move threat bonus, pawn structure, passed pawns, king shelter/storm/tropism, bishop pair, tempo | 336 | PASS, 3009/3009; mean 6.6, max 38.0 | vs v2: **+52.5 ± 39** (85 W, 55 L, 60 D) |
| `out/v3a.nnue` | v3 without the side-to-move threat bonus (ablation) | 320 | PASS, 3009/3009 | v3 vs v3a: +24.4 ± 28 (67 W, 53 L, 80 D). The stm bonus leans positive but is not resolved at 200 games |

The ± is fastchess's 95% interval. The numbers are in `out/match_*.json`, the full logs in `out/match_*.log`, and
the games in `out/match_*.pgn`. Exactness numbers are in `out/check_result.json` and `out/check_all.log`.
Elo is measured against the previous version on the same binary, so the steps add up to an approximate ladder:
material → v1 → v2 → v3 is about +670 Elo. That total is unverified as a direct match. These are 200-game smoke
tests, not SPRTs.

## Files

| file | what it does |
|---|---|
| `pesto.py` | PeSTO tables (Chess Programming Wiki, "PeSTO's Evaluation Function", by Ronald Friederich). Written from memory, because the network was off. The structure and piece values are the published ones; the individual table digits are **unverified** against the page. |
| `spec.py` | The whole evaluation as value functions of chess geometry, with the source of every term. Units: PeSTO cp × S, where S = 2.5 internal units per cp, so a PeSTO mg pawn is 205, close to Stockfish's PawnValue = 208. |
| `rows.py` | Decodes every one of the 131,952 input rows into chess meaning in the perspective frame: K32H3 block, king bucket and king square, piece and square; threat attacker/victim and squares; the two pawns of a pawn pair. |
| `build.py` | Puts spec.py into FT slots. `measure` measures the group bounds; `write v1 v2 v3` writes the nets. |
| `ideal.py` | The same evaluation computed straight from the board with python-chess. It shares no code with the row decoding. |
| `check.py` | The exactness checks A–D, including planted faults. |
| `match.py` | The fastchess smoke match. |
| `out/v0_material.nnue` | A byte copy of `../infra/out/material.nnue` (P/N/B/R/Q = 285/856/856/1427/2569), the baseline for v1. |

Run (local only, every command bounded by `timeout`):

    uv run --with numpy --with chess python -I build.py measure
    uv run --with numpy --with chess python -I build.py write v1 v2 v3
    uv run --with numpy --with chess python -I check.py v1 v2 v3 --n 2500 --book 500
    uv run python -I match.py out/v3.nnue out/v2.nnue        # 100 pairs, tc 10+0.1, concurrency 8, UHO book

## The evaluation

All terms are in internal units for the side to move ("stm"). Each side's terms are read in its own frame: that
side plays up the board, and the board is mirrored left-right when its own king is on files a–d. This is how the
engine's features see the board, and it means the tables are king-relative.

    e = tempo + [L(stm) − L(oth)] + t·[D(stm) − D(oth)] + T(stm) + BP(stm) − BP(oth)

- **L**: the linear part, with endgame values. In v1 it is the mg/eg average instead.
- **D**: middlegame minus endgame.
- **t**: the taper, `min(255, 10(N+B) + 21R + 43Q) / 256`, counted over both sides' pieces. This is PeSTO's phase (1, 1, 2, 4 per N, B, R, Q) scaled by 10.6. Full material gives 250/256 = 0.977.
- **T**: the side-to-move-only threat bonus.
- **BP**: the bishop pair.

The terms in each version:

- **v1, v2**: PeSTO material + PST for own pieces. The king table is averaged with its mirror, because in the perspective frame the own king is always on e–h.
- **v3** adds the following. Stockfish 11 classical values were converted to PeSTO cp by ×82/128 (mg) and ×94/213 (eg). Those values were recalled from memory and are **unverified**.
  - **Threats** (FullThreats rows, own piece attacks enemy piece):
    - Pawn→N/R: 0.75 × ThreatBySafePawn. "Safe" cannot be seen from the features.
    - N/B→P,N,B,R,Q: ThreatByMinor.
    - R→P,N,B,R: ThreatByRook.
    - Mutual same-type attacks get 0, because the feature set stores them in only one direction, chosen by square order.
    - FullThreats has no rows for pawn→B/Q, bishop→Q or rook→Q, so those threats cannot be expressed.
  - **Side-to-move threat bonus**: in separate slots whose fc_0 weight sits on the stm half only, worth 10% of (victim − attacker) PeSTO value when the victim is worth more.
  - **Pawn structure** (PP_3Wide rows):
    - Doubled: SF11 Doubled, per same-file pair.
    - Phalanx and supported: SF11 Connected seeds.
    - Passed pawns: half of SF11 PassedRank goes on every own pawn (K32H3 rows). Each enemy pawn in its front span takes the bonus back: 1.0× if on the same file, 0.5× if on an adjacent file. Half, because PeSTO's pawn table already pays for advanced pawns.
  - **King safety** (K32H3 rows, which carry the own king square). Middlegame only, so it sits in D. Weighted 1.0 / 0.5 / 0.25 by K32H3 block (2 = the enemy has a queen):
    - Shelter: +12 / +6 cp for an own pawn 1 or 2 ranks in front of the king, on the king's file or an adjacent one.
    - Storm: −10 / −5 cp for an enemy pawn 2 or 3 ranks in front.
    - Tropism: −(N 12, B 8, R 10, Q 30) cp × (4 − d)/3 for enemy pieces within Chebyshev distance 3.
  - **Bishop pair**: 40 cp (about half a pawn, as in Kaufman), in one product slot.
  - **Tempo**: 20 internal units.

## How the net computes it (extends ../infra/writer.py)

| slot kind | value column | gate column | output x | fc_0 row 30 |
|---|---|---|---|---|
| lin (L) | bias 2, 2·digit | bias 255 | Σ digits (the infra k−1 trick) | +c stm half, −c other half |
| dlt (D) | bias 1, 2·digit | phase g = 10(N+B)+21R+43Q (bias 0) | floor((2Σd+1)·g/512) ≈ Σd·t | +c / −c |
| stm (T) | as lin | 255 | Σ digits | +c stm half, 0 other half |
| bishop pair | 127 per own bishop | 127 per own bishop | 0, 31, 126, 127 for 0–3 bishops | +c / −c, with −31c per bishop put back into the lin bishop rows |

Everything else is zero. There is one stored layer stack: fallback all 0, fc_0 bias[30] = tempo. The eval is the
skip path fc_0_out[30] − fc_0_out[31].

**Digits.** Each weight is stored as the integer F = round(w·2048/75) and split into coarse (c = 127) and fine
base-(V+1) digits, exactly as in infra, but per **row group**. A slot holds digits of one group only, so its fill
is at most m·V, with digit cap V = 126//m (127//m for dlt).

**Group bounds m.**

- Proofs:
  - pieces per side: P 8, N/B/R 10, Q 9, own king 1;
  - own-pawn pairs: C(8,2) = 28.
- Design bounds, set to 2 × the corpus maximum over all 240,229 positions of `games/ka.pgn` (`out/group_bounds_measured.json`):
  - each threat group (attacker type × victim type);
  - us-vs-them pawn pairs: max 23, so m = 46;
  - in dlt slots only, also non-pawn piece groups: corpus max 2 per side, so m = 4. Bigger digits there cut the floor error.
- What happens past a design bound: the slot saturates rather than wrapping (the composed 5-queens-a-side position does this).

## Exactness, what each check measured

Sample: 3,009 positions.

- 2,500 distinct non-check positions from `games/ka.pgn` (infra's seed-7 sample).
- 500 non-check positions from the UHO book.
- 9 composed hand positions: start, queen up with either side to move, KPK, queenside-castled kings, 5 queens a side, a pawn forking N+R, doubled/isolated pawns, and a passed pawn on the 6th.

**A. engine == simulate (tolerance 0).** The engine's `NNUE evaluation` equals infra's bit-exact SFNNv20
simulator, run on the same file. The simulator was 2500/2500 on the real default net in infra.

| net | result |
|---|---|
| v1 | 3009/3009 |
| v2 | 3009/3009 |
| v3 | 3009/3009 |
| v3a | 3009/3009 |

**B. Linear regime.** The maximum slot fill on corpus and book positions is 120, below the cap of 126/127, and
0 corpus or book positions exceed the cap. The only position over the cap is the composed 5-queens-a-side one in
v2/v3. It is reported, and C is not asked of it: the engine gives 264 there against an ideal of 184.7 (v2),
because the dlt queen slots saturate.

**C. abs(engine − ideal) within an a priori bound** (`ideal.py`, independent of the decoding). The bound is
1 (truncation) + 0.5/27.3 per active weighted row + abs(c)/27.3 per non-empty phase-gated slot.

| net | positions within bound | max abs(engine − ideal) | mean abs(engine − ideal) | notes |
|---|---|---|---|---|
| v1 | 3009/3009 | 1.0 | 0.48 | bound ≤ 1.59 |
| v2 | 3008/3008 | 36.9 | 5.0 | |
| v3 | 3008/3008 | 38.0 | 6.6 | |

In internal units, where 100 cp ≈ 300 at middle material. The v2/v3 error is the floor of the phase product, at
most one x unit per gated slot. Before switching the dlt value bias from 0 to 1 and using design bounds for dlt
piece groups, the v3 mean error was 10.8 and the max 55.5 on a 259-position run. C is coarse by construction: the
bound averages 91 (v2) and 149 (v3), and neither planted net fault left it. A is the exactness test.

**D. Term-level decode.** For every position and both sides, the L, D and T sums read through the decoded rows
equal the same sums computed from the board by ideal.py. The maximum difference is 0.0 (v1, v2) and 8e-12 (v3,
float eps). So every piece-square, threat and pawn-pair term that occurs is mapped to the right row.

**Planted faults** (v3; each one must fire):

| fault | check | result |
|---|---|---|
| one FT digit +1 on the most active row | A | 599 mismatches, fired |
| phase-gate weight +16 on the most active rook row, first dlt slot | A | 409 mismatches, fired |
| ideal.py told that rook→queen is a feature | D | max term diff 137, fired |
| ideal.py with the king-file mirror removed | D | max term diff 510, fired |

## Caveats

- PeSTO and SF11 numbers were typed from memory: the structure is right, but some digits may differ from the published tables. The nets are correct implementations of *these* numbers (A–D); whether the numbers are the canonical ones is unverified.
- Design bounds are not proofs. A legal position past a threat, pair or dlt-piece bound saturates those slots, so the net then deviates from the ideal, as the 5-queens hand position shows.
- The weight scale S = 2.5 was chosen by hand (Stockfish PawnValue), not tuned.
- Smoke matches are 200 games. v3's +52.5 has a 95% interval of about ±39.

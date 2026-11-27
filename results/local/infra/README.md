# wspnet/infra: a programmable net writer for SFNNv20 (Stockfish master 8833740)

Every weight is placed by hand from closed-form integer formulas. There is no training and no optimiser.
Measured result: **PASS**. The full numbers are in `out/check_result.json` and the log in `out/check_all.log`.

| file | what it does |
|---|---|
| `features.py` | Ports the C++ source of all three feature sets: FullThreats, PP_3Wide and K32H3. It returns the exact active global FT rows for a board and perspective, plus the raw and stored layer stack. |
| `writer.py` | `write(path, components, const)` writes a valid .nnue whose engine static eval is a given linear target. `predict(plan, board)` returns the exact engine integer, the ideal value and the slot fill. `simulate(net, board)` is a bit-exact integer simulator for any SFNNv20 net. Also has `material_target`, `slots_needed` and `max_weight`. |
| `check.py` | `bounds` measures how many features are active per class over all of ka.pgn. `all` runs the exactness checks. Every stage refuses when it compares 0 positions. |

Run: `uv run --with numpy --with chess python -I check.py all --n 2500` (this Mac only, local engine).

## Target the writer supports

All values are in engine eval units, the number the engine prints as `NNUE evaluation <int> (side to move, internal units)`.

    e(pos) = const[s] + sum_k mask_k[s] * ( sum_{f in A(stm)} w_k[f] - sum_{f in A(other)} w_k[f] )

- `s` is the raw layer stack (0..191).
- `A(p)` is the set of active rows for perspective `p`. Rows are relative to the perspective (us/them, oriented squares), so one weight vector `w_k` (float[131,952]) serves both sides.
- `mask_k` makes component `k` stack-dependent. Stacks encode phase: piece-count band, which side has a queen, pawn layout, and minor/major count. This is the "phase-dependent part".
- `const[s]` is a per-stack constant, such as a tempo term.
- Raw stacks with identical (mask, const) share one stored stack through the fallback table.

## Construction

The full detail is in the header of `writer.py`.

**FT slots.** FT slot j (0..511) pairs column j (value) with column j+512 (gate).

- The gate column has bias 255 and no weights, so its clamp is 255 for every position.
- The value column has bias 2 and weights `2*d[f][j]`, so `a = 2k` with `k = 1 + Σ_active d`.
- The pair activation then gives `floor(2k·255/512) = k−1` exactly for 1 ≤ k ≤ 127. So **x_j = Σ_active d[f][j]**, which is linear while the fill Σ ≤ 126.
- Below 126 the accumulator stays ≤ 254 (no clamp) and every u8 stays < 128. That makes the result safe on the NEON u8 path and the dot-product path.
- The i16 accumulator wraps, but every final sum is in range, so incremental updates (wrapping adds) give the same result as a full refresh.

**fc layers.** Every stored stack writes only `fc_0` row 30:

- `+c_j·mask` on input j (stm half),
- `−c_j·mask` on input 512+j (other half),
- bias `round(const[s]·2048/75)`.

All other rows, fc_1, fc_2 and every other bias are 0. So `fwdOut = fc_2(=0) + fc_0_out[30] − fc_0_out[31]`. This is the skip connection, with no activation in the path.

**Output scaling.** The engine computes `eval = trunc(trunc(fwdOut·9600/16384)/16) = trunc(fwdOut·75/2048)` (C++ truncation toward zero). So **1 eval unit = 2048/75 = 27.31 fwdOut units**. A weight `w` is stored as the integer `F = round(w·2048/75)`.

**Digit split.** Each F is split into digits:

- Each feature class has a bound m on how many of its features can be active at once. The digit cap is V = 126 // m.
- `F = 127q + r`. The q part is spread over `ceil(q_max/V)` coarse slots with c = 127.
- r is written in base V+1 on fine slots with c = (V+1)^i.
- Positive and negative F use separate slots (c > 0 or c < 0).
- `build` checks that the digits rebuild F exactly before it writes.

**Design bounds m, the linear range of each class:**

| class | m | V | basis |
|---|---|---|---|
| psq (K32H3) | 32 | 3 | proof: at most 32 pieces, one feature each |
| pair (PP_3Wide) | 120 | 1 | proof: at most C(16,2) = 120 pawn pairs |
| threat (FullThreats) | 126 | 1 | design bound, not a proof. Measured max over all 480,458 perspectives of the 240,229 non-check ka.pgn positions is 45 (p99.99 = 44). |

A legal composed position with more than 126 threats could saturate a slot and break linearity. `predict()` returns the slot fill so a caller can detect it. Pass `bounds={"threat": 63}` to halve the threat slot cost (2.8× margin becomes 1.4×).

## Supported value range

The range is fixed by the 512-slot budget per perspective. `writer.build` refuses, rather than clamping, a target that does not fit.

- `slots(class, sign) = ceil(floor(F_max/127)/V) + n_fine(V)`, with n_fine = 4 for V = 3 and 7 for V = 1. This is `writer.slots_needed`.
- The sum over components, classes and signs must be ≤ 512.
- Largest single weight for one sign of one class using all 512 slots: psq 7,092 eval units; threat or pair 2,353 (`writer.max_weight`).
- Measured examples:

| target | slots used |
|---|---|
| psq ±150, threat/pair ±40, plus a half-scale stack-masked component | 154 |
| psq ±1000, threat/pair ±150 | 308 (the rule predicted 308) |
| material with Q = 2569 | 188 |

- A per-stack constant can be any value that fits an i32 fwdOut (|const| < 78M eval units).
- Total eval: no limit from the net. The search clamps values to the tablebase range, but the static eval line does not.

**Tolerance.** The integer prediction from `predict()` is exact (tolerance 0). Against the real-valued target, the error is `|engine − ideal| ≤ 1 + (75/2048)·Σ_active 0.5`. The 1 comes from truncation; each active feature adds at most 0.5 fwdOut of rounding. Measured maxima: 1.39 (random), 1.27 (wide), 1.0 (material).

## Measured exactness

2,500 distinct non-check positions sampled from `games/ka.pgn` (seed 7). The sample covers K32H3 blocks 0/1/2 (544/2102/2354 perspective counts), kings on files a–d (mirrored, 1,295), all three pawn layouts, 65 raw stacks and 1,252 positions with black to move.

| stage | result |
|---|---|
| Features + simulator on the real default net nn-684d0e60e71d (dense, 92 stored stacks) | 2500/2500 engine == simulate |
| Random linear target (2 components, one masked to band ≥ 4; random const on all 192 stacks, 192 stored) | 2500/2500 engine == predict; max fill 68/126; evals −2291..2515 |
| Wide random target (psq ±1000, threat/pair ±150) | 2500/2500 exact; max fill 67; evals −11233..10196 |
| Weight past the budget (psq 7,157 > 7,092) | refused |
| Planted: one FT digit +1 on the most-often-active programmed row | 478/2500 mismatches, so the check FAILs as it should |
| Planted: fc_0 bias +100 on the most common stored stack | 277/277 positions on that stack mismatch, so it FAILs |
| Material known answer | 2500/2500 exact |

**Material known answer.** Piece values are P,N,B,R,Q = 1,3,3,5,9 × s. The scale s comes from closed-form least squares of the default net's evals on material difference: **s = 285.4 internal units per pawn**, giving P = 285, N = B = 856, R = 1427, Q = 2569. Results:

- Correlation with the default net's evals is 0.752.
- Sign agreement is 93.1% when |material difference| ≥ 2 pawns.
- Startpos gives 0.
- Queen up gives +2569 with white to move and −2569 with black to move.
- Knight up gives +856.
- Pawn up gives 284 (ideal 285, truncation).

## Notes

- `out/*.nnue` files are about 140 MB each. `random_linear.nnue` and `material.nnue` are kept as reference nets; delete them freely.
- The header, hashes and description are copied from the template net (default nn-684d0e60e71d), which the engine checks.
- Positions in check have no static eval, so they are excluded.

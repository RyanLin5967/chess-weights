# wspnet/bootstrap: the closed-form net without Stockfish's trained net (2026-11-27)

Every label here comes from our own WSP nets' depth-10 search. There is no gradient descent and no optimiser: each fit is the
ridge normal equations solved by Jacobi-preconditioned CG (closedform/solve.py pcg). All compute ran on this Mac.

## Setup
- **Positions:** a fixed set of 3,623,812, held the same for every generation.
  - 1,372,365 come from 14,000 new games played only by the hand-written nets (programmed v3 vs v2 and v3 vs v1, 6,000 nodes per move, UHO book). See `games/`.
  - 2,251,447 are round-1 positions, read from `closedform/data/*_fens.tsv`. Those files hold positions only, no labels.
- **Split:** by game, using closedform `split` with seed 0.
- **Labels:** `label_bs.py`, depth 10, Threads 1, Hash 16, with `EvalFile` set to the current labeller. Mate scores are dropped.
- **Labeller guard:** each worker checks 6 positions. Its static eval must equal the bit-exact simulation of that net file (`writer.simulate`), with tolerance 0. The labeller also refuses the default net by name or sha. Both guards were tested by forcing them to fire.
- **Fit:** `solve_bs.py` uses round 1's best system, "pairs": psq + threat + pair rows, an endgame (eg) delta component, groups, material and stack constants. It uses round 1's lambdas (psq 100, threat 300, pair 1000). For gen1, a scale grid of {0.3, 1, 3} gave val R^2 of .8769, .8772 and .8746, so scale 1 was chosen and fixed from gen2 on.
- **Net file:** written with `writer.write(template=programmed/out/v3.nnue)`, so the default-net file is never opened.
- **Exact check:** `closedform/exact.py`.
  - Linearity is scanned over all 3.62M positions.
  - The engine must equal the prediction on 3,000 test positions, with tolerance 0.
  - A planted fault must fire.
- **Smoke:** `smoke.sh` plays 200 games, 10+0.1, concurrency 12, using the round-1 smoke settings and srand 4242.
- **Labeller rule:** a generation gains when its score is above 50% against the best net so far. The next labeller is always the newest net, because relabelling with an unchanged best net reproduces the same net exactly. The loop stops after two consecutive generations without a gain.

## Results (run_all.py, logs/state.json)
| net | labels from (sha256) | test R^2 vs own labels | R^2 vs default-net labels (diagnostic) | smoke |
|---|---|---|---|---|
| v3 (gen0, hand-written) | none | 0.7717 (static, 20k sample) | 0.6579 | (reference) |
| gen1 fee4b363... | v3 ea4bc40d... | 0.8762 (diag subset 0.8689) | 0.7588 | vs v3 **+63.2 +/- 42.0**; repeat with srand 4343: +68.6 +/- 41.5 -> BEST |
| gen2 8bf81284... | gen1 fee4b363... | 0.8863 (0.8806) | 0.7715 | vs gen1 **-45.4 +/- 35.3** (no gain) |
| gen3 c7b7c2b8... | gen2 8bf81284... | 0.8862 (0.8814) | 0.7702 | vs gen1 **-135.0 +/- 39.5** (no gain) -> STOP |

The "vs default-net labels" column uses round-1 test positions only (n of about 223k), and a fit never reads it. For reference, round-1 pairs scored .7849 and the default net's static eval .8583 on round 1's own 20k sample (closedform/out/ref_same_sample.json).

**Exact check:** gen1, gen2 and gen3 all PASS.
- Engine equals prediction on 3000 of 3000 positions each.
- Linear on all 3,623,812 positions, with max slot fill 66, 71 and 72 (out of 126).
- The planted fault fires (1 mismatch).
- Slots used: 425, 421 and 419.

**PCG convergence:** each run stopped at the 4,000-iteration cap, short of the 1e-7 tolerance. Final relative residuals were 3.6e-7 (gen1), 1.3e-6 (gen2) and 1.0e-6 (gen3). The metrics are computed from the weights actually written.

**Head to head against round 1's default-label net** (closedform/out/pairs.nnue, rated 2928 +/- 17):
- gen1 vs pairs: **+153.4 +/- 40.6** (srand 4242) and **+111.4 +/- 42.5** (srand 4343), about +132 over 400 games.
- The control, v3 vs pairs, gave -38.4 +/- 43.7 under the same conditions. This reproduces round 1's -33.1 +/- 43.1, so the harness agrees with round 1.
- These results are not transitive. gen1 is +63 above v3 and v3 is -35 below pairs, so transitivity predicts gen1 at about +30 over pairs, not +130. The head-to-head numbers were repeated with two seeds.
- None of this is a rating. rate.py anchors are the default net at UCI_Elo levels, which this task excludes.

**Label drift** (out/label_stats.json):
- Across v3, gen1 and gen2 labels, the cp standard deviation was 423, 424 and 448.
- The share of |cp| > 300 was 26.7%, 29.4% and 31.4%.
- The median |cp| was 131, 136 and 147.
- The spread of the gen-k stack constants grew from +/-1.1k to +/-1.5k.

The labels inflate each generation while R^2 against each net's own labels rises. Whether this inflation causes the gen2 and gen3 losses is unverified.

**No default net:** `audit.py` writes `out/evalfile_audit.json`.
- It covers every EvalFile from `logs/evalfile.jsonl` and from fastchess's own config.json files (9).
- The only EvalFiles used were v1, v2 and v3 (programmed), gen1, gen2 and gen3, and closedform pairs.nnue, which was used only as an opponent in the head-to-head.
- `default_net_used` is empty, and the logged sha256 values match the files.
- The audit fires on a planted default-net entry.
- Only diag.py names round-1 label files.
- The Stockfish binary still embeds the default net as the EvalFile default and loads it at startup. It is replaced before any eval or search, and the fingerprint guard checks this on the outcome.

# Best nets (2026-11-27)

| Net | How it was made (no gradient training) | Direct match vs official Stockfish | Other result |
|---|---|---|---|
| `cx1.nnue` | linear Cauchy-weighted accumulator + hand-built hinge (nonlinear) fc stack, every layer an exact ridge solve, labels = Stockfish search scores (sf_n5000), never the official net's eval | not yet played | beat lin_cauchy1200 by +63 +/- 38 Elo (200 games, 10+0.1) |
| `lin_cauchy1200.nnue` | linear exact ridge fit, Cauchy row weight w = 1/(1+(y/1200)^2) | 541 Elo weaker than official [474, 608 weaker], 400 games, 10+0.1 (5 W / 371 L / 24 D) | +182 vs the closed-form pairs net |

Restore: `python3 restore_weights.py` (verifies SHA-256), or `gzip -dk weights/best/<net>.nnue.gz`.
Load in Stockfish: `setoption name EvalFile value <path>/cx1.nnue`.

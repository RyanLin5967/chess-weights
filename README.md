# chess-weights

All **35 research chess checkpoints** and their results from the 2026-11-27 snapshot.
Weights are stored as lossless `.nnue.gz` files so each fits GitHub's file limit.
Every checkpoint is self-contained. No public base network or delta patch is required.
The repository also includes all original result reports, ratings, game summaries,
PGNs, logs, and state snapshots from the export.

## Restore the weights

```sh
git clone https://github.com/RyanLin5967/chess-weights.git
cd chess-weights
python3 restore_weights.py
```

This restores all 35 `.nnue` files under `restored/weights/` and verifies their
SHA-256 checksums. Allow approximately 4.9 GB for the restored files.
Use `python3 restore_weights.py --verify-only` to verify without writing them.
An individual checkpoint can also be restored with `gzip -dk path/to/model.nnue.gz`.

## Results and interpretation

- `RESULTS.json`: result highlights and original SHA-256 inventory.
- `COMPRESSION.json`: compressed file paths and restored checkpoint hashes.
- `results/`: all original reports and evaluation evidence.
- `weights/local/`: eight local research approaches.
- `weights/mac2/`: CFVI generation candidates/incumbent and final SPSA checkpoint.

**+62 Elo means phase/p13x versus our closedform/pairs checkpoint.**
It is not a result against official Stockfish. No checkpoint in this snapshot
has demonstrated parity with official Stockfish. The direct official matches
were negative and ran under load. Anchor ratings are approximate engine ratings,
not verified FIDE ratings. XF's smoke match is invalid due to 27 time forfeits.
CFVI generation 1 was rejected; generation 2 was screening at the snapshot.
The final SPSA checkpoint has not completed its registered verification SPRT.

Network format: SFNNv20, matching pinned Stockfish source commit `88337401b7a4`.
Load a restored checkpoint through the UCI `EvalFile` option.
Datasets, random/debug fixtures, and downloaded official networks are excluded.

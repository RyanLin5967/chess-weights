Chess WSP checkpoints and results -- 2026-11-27 snapshot

weights/local/: research checkpoint outputs, grouped by approach.
weights/mac2/: CFVI generation checkpoints/incumbent and final SPSA checkpoint.
results/: original reports, checks, ratings, game summaries/PGNs and state snapshots.
RESULTS.json: result highlights and SHA-256 inventory of all source files.

+62 Elo means phase/p13x versus OUR closedform/pairs checkpoint.
It does not mean +62 versus official Stockfish.
No checkpoint here has demonstrated parity with official Stockfish.
UCI_Elo anchor ratings are approximate engine ratings, not FIDE ratings.
XF's game result is VOID: 27 of 200 games ended in time forfeits.
CFVI generation 1 was rejected; generation 2 was screening at the snapshot.
The final SPSA net has not completed its registered verification SPRT.

Format: SFNNv20, pinned Stockfish source commit 88337401b7a4.
The matching local binary is:
/Users/idide/projects/sf-wsp.noindex/src/stockfish/src/stockfish
An older Stockfish release may reject this network format.
Load a checkpoint through the UCI option:
setoption name EvalFile value /absolute/path/to/checkpoint.nnue

The datasets and temporary random/debug network fixtures are not included.

# wspnet/compiler: Stockfish 11's classical evaluation compiled into SFNNv20 weights

Every weight is placed by closed-form integer formulas from the SF11 source. There is no training, no optimiser and no
gradient. Two closed-form least-squares solves set constants that SF11 does not define for this engine: the unit scale
K (1 number) and the linear stand-in for MobilityBonus (2 numbers per piece type and phase). Two corpus averages set the
rest: the design bounds (2x the corpus maximum, as in ../programmed) and the mean SF11 phase per layer stack (king-danger
taper). All compute ran on this Mac.

Source: official-stockfish/Stockfish tag `sf_11`, `src/{evaluate,material,pawns,psqt,endgame}.cpp`, `types.h`,
`bitboard.{h,cpp}`, `evaluate.h`, `pawns.h`, `material.h`, downloaded from
`https://raw.githubusercontent.com/official-stockfish/Stockfish/sf_11/src/<file>` into `sf11_src/` (about 170 KB, GPL-3.0,
`sf11_src/Copying.txt`). **Every SF11 number is parsed from that text by `sf11.py`; none is typed by hand**, so the
"typed from memory" caveat of `../programmed` does not apply here. (Its SF11 threat and pawn values turned out to match.)

## Results

| net | SF11 terms added | FT slots (of 512) | exactness, 3,011 positions | smoke vs programmed v3, 200 games 10+0.1, conc 8 |
|---|---|---|---|---|
| `out/c1.nnue` | material, PSQT (mg/eg tapered by SF11 phase), quadratic imbalance, tempo | 123 | PASS | **-193.2 +/- 53.0** (38 W, 139 L, 23 D; 1+3 time losses) |
| `out/c2.nnue` | + pawn structure, passed pawns (gated per file, both kings' proximity), threats, shelter/storm, pawnless flank | 432 | PASS | **-24.4 +/- 41.6** (70 W, 84 L, 46 D; 3+4 time losses) |
| `out/c3.nnue` | + mobility (ray lengths from threat rows) | 417 | PASS | **+45.4 +/- 43.1** (93 W, 67 L, 40 D; 1+1 time losses) |
| `out/c4.nnue` | + king danger through the nonlinear fc layers (ReLU, square, per-stack taper) | 450 | PASS | **+31.4 +/- 42.9** (95 W, 77 L, 28 D; 4+2 time losses) |
| `out/c5.nnue` | + KingProtector, RookOnFile (semi-open/open), minPawnDist | 494 | PASS | **+24.4 +/- 46.4** (91 W, 77 L, 32 D; 0 time losses with a 200 ms clock margin; a first run at load 68 had 37 time losses and is kept as `out/match_c5_vs_v3_INVALID_37timelosses.*`, not used) |
| `out/c5k.nnue` | c5 with scale K_rma = 1.418 instead of K = 1.038 (threats, pawn pairs, shelter with rounded digits to fit) | 502 | PASS | **-17.4 +/- 44.1** (75 W, 85 L, 40 D; 0 time losses, 200 ms margin) |

Reading: the SF11 compile reaches programmed v3's strength by c2 and passes it by about +25 to +45 Elo from c3 on (c3
+45.4, c4 +31.4, c5 +24.4; each 200-game interval is about +/- 45, so c3, c4 and c5 are not separable). Mobility (c3) is
the one addition with a visible step (+70 over c2, still inside two intervals). King danger, KingProtector, RookOnFile
and minPawnDist add nothing measurable at this sample size. The larger scale (c5k) leans worse than c5 (-42, not
resolved). On the PLAN.md rating scale this puts the compiled nets near 2839 + 25..45, i.e. below the closed-form net
(2928); that placement is an inference from chained smokes, not a rating run.

The +/- is fastchess's 95% interval. Programmed v3 itself rated 2839 +/- 17 (../../PLAN.md). Match files:
`out/match_<net>_vs_v3.{json,log,pgn}`. The Mac was shared with other lanes during the smokes (load 30-70 on 18 cores);
time losses are listed per match and stayed under 5%.

**How much of the real SF11 evaluation each net carries** (`fidelity.py`, `out/fidelity.json`): the official SF11
binary, built from tag sf_11 on a fresh Colab CPU VM (`sf11_eval/colab_sf11_eval.py`, output `sf11_eval/colab_out.txt`),
gave its static eval on the same 3,011 positions; 84 specialized-endgame values (|v| >= 8000, VALUE_KNOWN_WIN) are left
out, 2,927 remain (SF11 eval sd 744 internal units).

| compiled function | Pearson r with SF11 | Spearman | R^2 (through-origin scale) | mean abs diff | sign agreement, abs(SF11) >= 100 |
|---|---|---|---|---|---|
| c1 | 0.921 | 0.807 | 0.845 | 199 | 0.875 |
| c2 | 0.938 | 0.851 | 0.879 | 178 | 0.901 |
| c3 | 0.943 | 0.876 | 0.888 | 171 | 0.917 |
| c4 | 0.943 | 0.872 | 0.888 | 176 | 0.917 |
| c5 | 0.945 | 0.878 | 0.892 | 171 | 0.921 |

The king-danger proxy (c4) does not move the eval closer to SF11's: without safe checks, weak squares and flank attacks
it is not SF11's king danger. The remaining 11% of variance is the list under "NOT expressible" below.

Exactness (`out/check_result.json`, logs `out/check_*.log`), every net:

- **A. engine == simulate: 3011/3011** for c1..c5 and c5k. The engine's `NNUE evaluation` equals infra's bit-exact SFNNv20
  simulator on the same file (the simulator itself is 2500/2500 on the official net, ../infra).
- **B. linear regime:** 0 corpus/book positions over any slot cap or product design bound.
- **D. term by term:** for every term and both perspectives, the net's own contribution (sum of c_j x_j over that term's
  slots, x from the bit-exact FT simulation) equals `ref.py`'s board-side value of the term within its a-priori rounding
  bound: 0 violations for every term of every net. King danger is checked as integers: the net's fc_0 pre-activation and
  final penalty equal the board-side integer pipeline exactly (max difference 0) on all 6,022 perspectives.
- **C. |engine - ref.evaluate| within the summed bound: 3011/3011**; mean |engine - ideal| 2.2 (c1) to 4.1 (c4/c5) and 5.3 (c5k)
  internal units, max 39.
- **Planted faults, all fire:** FT digit +1 (599 mismatches), phase-gate weight +16 (254), ref with SF11's raw asymmetric
  pawn table (D), ref counting bishop->queen as a threat (D), ref letting queens stop bishop mobility rays (D, 21),
  ref without SF11's king-ring clamp (kd o0, 162 perspectives).

Sample: infra's seed-7 sample of 2,500 non-check `games/ka.pgn` positions + 500 UHO book positions + 11 composed
positions. Scale: K = 1.0378 (`scale.json`: least squares of the official net's static eval on c1, 3,000 other corpus
positions; corr 0.734), i.e. SF11 internal units are almost exactly this engine's units. That OLS slope is attenuated
by the c1 eval's own error (r = 0.73); the reduced-major-axis slope sqrt(<d,d>/<e,e>) = 1.418 (also closed form,
`scale.json`) treats both sides as noisy. c5k is c5 at that scale: the search's margins see a 37% larger eval.

## Files

| file | what it does |
|---|---|
| `sf11.py` | Parses every SF11 constant from `sf11_src/` and records its file:line. |
| `terms.py` | Each compiled term as a value function of the perspective frame (own side up, mirrored when the own king is on a-d), with the SF11 line it implements. |
| `mobility.py` | Compiled mobility m', SF11's true mobility (for the fit only), the linear MobilityBonus stand-in (`mob_fit.json`), row values, design bounds. |
| `kingdanger.py` | King danger: FT rows, product slot, fc-layer weights, per-stack phase (`tbar.json`), and its board-side integer pipeline. |
| `compile.py` | The slot machinery and the nets: `compile.py write c1 c2 c3 c4 c5`. |
| `ref.py` | Board-side reference of exactly the compiled terms, python-chess, no row decoding, no king-side mirror; `fitK`. |
| `check.py` | Checks A-D and the planted faults. |
| `match.py` | 200-game smoke (copy of ../programmed/match.py writing to ./out). |

Run (this Mac, each command bounded by `timeout`):

    uv run --with numpy python -I sf11.py
    uv run --with numpy --with chess python -I ref.py fitK
    uv run --with numpy --with chess python -I mobility.py fit && ... mobility.py measure && ... kingdanger.py tbar
    uv run --with numpy --with chess python -I compile.py write c1 c2 c3 c4 c5
    uv run --with numpy --with chess python -I check.py c1 c2 c3 c4 c5
    uv run python -I match.py out/c5.nnue ../programmed/out/v3.nnue

## How the net computes SF11

FT slot j: value column j, gate column j+512, `x_j = floor(clip(v)*clip(g)/512)`, clip to [0, 255]. The evaluation is the
skip path `fc_0_out[30] - fc_0_out[31]` (weight +c_j on the side-to-move half, -c_j on the other), plus the fc_2 output
for king danger. Slot kinds, all exact integer constructions:

| kind | value column | gate column | x | used for |
|---|---|---|---|---|
| lin | 2 + 2*sum(digits) | 255 | sum of digits | eg values |
| dlt | 1 + 2*sum(digits) | phase g | floor((2S+1)g/512) ~ S*g/256 | mg - eg, tapered |
| egg | 1 + 2*sum(digits) | 255 - g | ~ S*(255-g)/256 | eg-only terms in one family |
| gated | as lin/dlt/egg, minus 128 per active blocker row | as lin/dlt/egg | 0 if any blocker, else as lin/dlt/egg | per-file conditions: isolated, unopposed, passed, rook on (semi)open file, pawnless flank, minPawnDist |
| prod | sX * nX (count rows) | sY * nY | (sX*sY/512) * nX * nY exactly | imbalance (n^2 and n*m terms), king attackers count x weight |

Phase gate g = clip(18N + 19B + 29R + 57Q - 91, 0, 255) over both colours: the integer weights closest to
2 * SF11 game_phase (material.cpp:130-135); mean |g/256 - phase/128| = 0.0026, max 0.012 on the sample.

**King danger uses the nonlinear layers** (first time in this project): fc_0 row 0 (row 1 for the other side) receives
o0 = 4*KD - 400; `c0 = clip(o0 >> 7, 0, 127) = ReLU((KD - 100)/32)`; fc_1 rows square it (`(127 c0)^2 >> 19`); fc_2 gives
the penalty 2a*sq1 + b*c0 with a, b per layer stack from the stack's mean SF11 phase, so mg KD^2/4096 and eg KD/16 are
tapered. KD fires (c0 > 0) on 39% of corpus king-perspectives; penalty median 0, p90 61, max 1,132 internal units.

## What is compiled, and how exactly

| SF11 term (source) | compiled as | exact? |
|---|---|---|
| PieceValue + Bonus (psqt.cpp:111-127) | psq rows, lin + dlt | exact, except PBonus (pawn table) is mirror-averaged, see below |
| game phase taper (evaluate.cpp:817-820, material.cpp:130-135) | dlt/egg gates | integer gate, mean deviation 0.26% of the phase |
| imbalance (material.cpp:84-107, 209-215) | 36 product slots | exact for <= 8 P, <= 3 N/B/R/Q, <= 2 B per side (larger counts saturate; 0 sample positions) |
| Tempo (evaluate.h:32) | fc_0 bias | exact |
| Doubled (pawns.cpp:103, 149-150) | own-pawn pair rows | ignores "!support" |
| Connected (pawns.cpp:105-106, 133-138) | own-pawn pair rows | per pair; opposed not visible per pawn, so 2.5 = mean of (2 + phalanx - opposed) |
| Isolated, WeakUnopposed for isolated pawns (pawns.cpp:141-143) | gated per file (blockers: own pawns on adjacent files; + opposing pawn pairs) | exact per file |
| passed flag, condition (a) (pawns.cpp:100-101, 121) | gated per file: blockers = non-lever stopper pairs | a file counts as passed only if no pawn on it has a non-lever stopper; (b), (c) dropped |
| PassedRank, own-king proximity, PassedFile (evaluate.cpp:596-609, 644) | gated per file on own-pawn psq rows (they carry the own king square) | exact for those parts |
| enemy-king proximity (evaluate.cpp:604) | computed in the DEFENDER's accumulator: their pawn rows know my king square, my pawns gate it | exact |
| ThreatByMinor (evaluate.cpp:506-508) | threat rows | exact for non-pawn victims that have rows; pawn victims x0.5 (protection not visible); per attacker, SF11 per victim |
| ThreatByRook (510-512) | threat rows x0.5 | "weak" not visible |
| ThreatBySafePawn (533-535) | P->N, P->R rows | "safe" not visible; P->B, P->Q have no rows |
| shelter / storm (pawns.cpp:185-215) | psq rows relative to the own king | exact with <= 1 own and <= 1 enemy pawn per zone file; blocked storm folded into unblocked |
| PawnlessFlank (evaluate.cpp:463-465) | gated per flank type | exact |
| mobility (evaluate.cpp:225-230, 266-289) | psq row: alpha + beta * empty-board count; threat rows: -beta * ray beyond the blocker | m' exact per mobility.py's definition; vs SF11's m: corr 0.73 (N), 0.81 (B), 0.84 (R), 0.89 (Q); linear stand-in R^2 0.45-0.74 |
| king danger (evaluate.cpp:446-461) | see above | proxy: cnt*wgt (empty-board attacks), 69*attacks, -873*no queen, -6/8*shelter, +37 |
| KingProtector (evaluate.cpp:305-306) | own N/B psq rows | exact |
| RookOnFile (evaluate.cpp:342-344) | gated per file | exact |
| minPawnDist (pawns.cpp:239-248) | 7 gated slots: minPawnDist = 1 + sum_{d=2..7}[no own pawn within d-1] - 7[no own pawn] | exact |

## SF11 terms NOT expressible, and why

The three feature sets see: each piece's square relative to the own king (K32H3), every attack of a non-king piece ON
another piece (FullThreats, minus P->B/Q, B->Q, R->Q and one direction of same-type pairs), and every pair of pawns within
three files (PP_3Wide). They do not see empty squares' attack status, two pieces jointly (except pawn pairs and
attacker/victim), castling rights, the rule-50 counter, or which side of the board the own king is on.

- **PBonus asymmetry** (psqt.cpp:93-102): the oriented frame mirrors the board when the own king is on files a-d and no row
  says whether it did, so only the mirror-symmetric half of the pawn table exists.
- **Squares attacked by enemy pawns, blocked pawns above rank 3, pins, own king** in the mobility area (evaluate.cpp:226-230,
  273-274): attack status of empty squares and piece-pair geometry are not rows. **MobilityBonus concavity**: one piece's
  bonus is nonlinear in its own count; a slot sums over all pieces, so only a linear stand-in fits.
- **x-ray continuation** past a queen (bishops, rooks) or own rook: the ray beyond the first piece has no row.
- **Safe and unsafe checks, weak king-ring squares, king flank attack/defence, blockers for king, mobility difference,
  knight defender** in king danger (evaluate.cpp:386-456): all need attack maps of empty squares.
- **Hanging, RestrictedPiece, ThreatByKing, ThreatByPawnPush, KnightOnQueen, SliderOnQueen, "weak"/"defended" status**
  (evaluate.cpp:486-561): defended/attacked status of squares and pieces by everything.
- **Passed-pawn free-path bonus k and candidate halving** (evaluate.cpp:611-642): attacks on the path squares.
- **Backward and WeakLever** (pawns.cpp:110-111, 151): per-pawn conjunctions over three or more pawns (neighbours behind on
  two files AND a lever-push/block; two levers). Gating can only be per file or per king square within 512 slots.
- **Outpost, ReachableOutpost, MinorBehindPawn, RookOnQueenFile, LongDiagonalBishop, WeakQueen, TrappedRook**
  (evaluate.cpp:294-361): a piece jointly with a pawn span, a pawn in front, a queen on the file, pawns on a diagonal,
  pins, or the piece's mobility <= 3 and the king's side. **BishopPawns** (314-315) needs pawns-on-colour x bishop x
  blocked centre pawns, a triple product.
- **Space** (661-691): union of enemy pawn attacks and all enemy attacks on empty squares, then a quadratic piece-count
  weight.
- **Initiative** (698-737): bounded by |eg| of the WHOLE evaluation and signed by it; an FT slot sees one perspective only.
- **Scale factors** (evaluate.cpp:743-761, material.cpp:195-204) and **specialized endgames** (endgame.cpp): they multiply the
  eg sum of both perspectives by a factor chosen by which side is stronger; the rule-50 term has no input at all.
- **Castling options in the shelter** (pawns.cpp:231-237): no castling-rights input.
- **Lazy evaluation and contempt**: a search speed device and a dynamic setting, not evaluation terms.

## Caveats

- Smokes are 200 games; intervals are about +/- 50 Elo.
- Design bounds are not proofs (5+ N/B/R/Q of one kind, 3+ bishops for the pair, 4+ of a kind in products, tripled pawns
  in the per-file gates); past them slots saturate. No sampled game or book position reached one.
- The mobility stand-in, the king-danger proxy and the 0.5 factors are this compiler's choices, documented above; the net
  computes exactly those (D), not SF11 itself.

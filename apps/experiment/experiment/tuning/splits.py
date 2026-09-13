"""Train/validation/test protocol for the workload predictor, designed from the data.

This module replaces the inherited proportional split (train [0, 22500), validation
[22539, 26205), test [26243, 40315), embargo 38 on ClarkNet 15 s) with an evidence-
driven protocol. Every number below was measured on 2026-09-13 from
``data/processed/clarknet_real_rps.parquet`` and ``data/processed/calgary_real_rps.parquet``
(``scripts/eda_timeseries.py`` bundles at ``results/models/gru/2026-09-13_eda-*/`` plus an
independent recomputation on the raw parquet).

PROTOCOL RATIONALE
==================

Corpus facts (measured)
-----------------------
ClarkNet: 40,315 gapless 15 s buckets, Mon 1995-08-28 04:00:30 UTC -> Mon 1995-09-04
03:59:00 UTC (6.999 days). The weekend is one contiguous region at the tail:
indices [27,838, 39,358) (Sat 00:00 -> Sun 23:59:45). Weekend level is 0.647x weekday.
Calgary: 2,027,652 gapless 15 s buckets, 1994-10-24 -> 1995-10-11 (352.02 days),
zero-inflated (84.1% zero buckets, skew 7.03), mean 0.358 counts/bucket, weekend level
0.523x weekday -- the same regime direction as ClarkNet.

The inherited split trains on weekdays only: train [0, 22500) and validation [22539,
26205) contain 0.0% weekend; test [26243, 40315) is 81.86% weekend and its mean level
is 34.08 vs the training 45.70 counts/bucket (level shift 0.746). Model selection was
therefore performed by extrapolation across a regime the model never saw. The protocol
below keeps the leakage-safe bones of the inherited split but makes every regime
composition explicit and moves selection onto blocked cross-validation.

1. Deployment evaluation stays a forward held-out block, reported separately
---------------------------------------------------------------------------
The deployment test region [26243, 40315) is kept exactly as frozen, for three
evidence-grounded reasons. (a) The k6 replay window 1995-09-02 04:35:30-04:55 UTC
(indices [28,940, 29,020)) sits inside it, and the closed-loop evidence depends on
that placement. (b) The deployment target is a Saturday-morning replay, so a
weekend-dominant test region is faithful to deployment conditions: Tashman (2000)
requires the out-of-sample test to mirror how the forecast will be used, including
regime; hiding the weekend from the test would test something we do not deploy on.
(c) No forward-only redesign can put weekend into training: the weekend is the tail
of the corpus, so any train region preceding the replay window excludes it entirely.
What changes is not the region but its role: the deployment block is out of the
training distribution by construction, so it is REPORTED SEPARATELY with its day-type
composition (18.14% weekday: Fri evening 17:21-24:00 + Mon 00:00-04:00; 81.86%
weekend) and is NEVER used for model selection (Hyndman & Athanasopoulos, fpp3,
ch. 5.10, https://otexts.com/fpp3/tscv.html: a test set is used once, never for
tuning). ``SplitSpec.used_for_selection`` is False for this spec and validated.

2. Model selection uses blocked cross-validation with expanding origin
----------------------------------------------------------------------
Following Bergmeir & Benitez (2012) ("On the use of cross-validation for time series
predictor evaluation", Information Sciences 191:192-213), evaluation blocks are
contiguous (no shuffling within blocks, preserving the lag-1 autocorrelation of 0.73
and daily autocorrelation of 0.45), and following fpp3 ch. 5 / Tashman's rolling
origin, each fold trains only on data that ends before its evaluation block starts.
Blocks are 1 day (5,760 buckets): one full diurnal cycle, the strongest seasonal
period, and the coarsest day-type unit the 7-day corpus supports. With a minimum of
2 training days and an embargo of sequence_length + horizon - 1 = 30 + 9 - 1 = 38
samples at every train->eval boundary, the legal folds are:

    fold b2: train [0, 11482)      eval [11520, 17280)  eval weekend  0.0%  shift 1.053
    fold b3: train [0, 17242)      eval [17280, 23040)  eval weekend  0.0%  shift 0.982
    fold b4: train [0, 23002)      eval [23040, 28800)  eval weekend 16.7%  shift 1.022
    fold b5: train [0, 28762)      eval [28800, 34560)  eval weekend 100.0% shift 0.650

Fold b6 (eval [34560, 40315), Sun-dominant) is STRUCTURALLY UNUSABLE: its expanding
train region [0, 34522) would contain the replay window. It is skipped with a recorded
reason, and the skip is asserted by ``assert_replay_placement`` if ever re-added.

Per-block day-type coverage is always computed and reported (question 2 of the
design brief: yes, report it). Accuracy aggregates as mean and spread across blocks
(sample std, ddof=1, plus min/max) -- never a single number; ``aggregate_block_metrics``
refuses to aggregate fewer than two blocks.

3. The out-of-distribution block is quarantined from selection
--------------------------------------------------------------
Fold b5 evaluates a 100% weekend block whose training region holds only 3.2% weekend
(Sat 00:00-03:50 pre-dawn). Selecting on it would select the best extrapolator, not
the best predictor (Bergmeir & Benitez 2012, fpp3 ch. 5.8 on comparing across
origins). Decision rule, applied by measurement at construction time: a fold is a
selection fold iff its eval-block day-type set intersects the train day-type set AND
either the eval block is majority-weekday (<50% weekend) or the train region holds
>= 10% weekend. b2/b3/b4 qualify; b5 is role="ood_report", reported separately with
its composition (this is also the extrapolation rehearsal for the deployment block).

4. Normalisation: log1p then robust center/scale, fitted on the train region only
---------------------------------------------------------------------------------
Evidence: ClarkNet skew 0.88 / Calgary 7.03; zero share 0.07% vs 84.1%; block level
shifts 0.65-1.05; corpus levels 45.7 vs 0.33 counts/bucket (137x). A plain z-score on
raw RPS would let level and spikes dominate. The protocol transforms with log1p
(zeros map to 0, right tails compress), then centers on the median and scales by the
IQR of the transformed training region. Calgary's log1p IQR is exactly 0 (p25 = p50 =
p75 = 0), so the scale falls back to the std of the transformed region; a zero scale
raises. Stats are fitted ONLY on a spec's train region (``normalizer_stats`` rejects
any other region loudly). Note the transform is not invariant to the k6 replay
amplification (x33, ``data/trace-replay/clarknet_replay_manifest.json``): the
deployment arm must fit stats on the amplified series it actually serves, matching
``gru_study``'s convention; split geometry is unaffected.

5. Calgary supplies the weekend regime for pretraining, with explicit leak rules
--------------------------------------------------------------------------------
ClarkNet cannot support weekend-in-distribution selection (see limitations). Calgary's
352 days contain 44 full weekends in the pretrain region [0, 1,769,354) (1994-10-24 ->
1995-08-27 23:59:45, weekend share 28.65%). Leak rules, all asserted:
  a. The Calgary pretrain region ends at 1995-08-28 00:00 UTC, strictly before the
     ClarkNet span (which starts 04:00:30 that day). The temporal overlap window
     [1,770,316, 1,810,634) (Calgary's buckets covering the ClarkNet week) plus a
     4-hour guard band are never used, and the post-cut tail (258,298 buckets) is left
     unused entirely so no contiguous region crosses the cut.
  b. Pretraining validation uses the pure-weekend Calgary block [cut-11,520, cut)
     (Sat 1995-08-26 00:00 -> Sun 1995-08-27 24:00), embargo 38.
     Its train region contains 43 other full weekends, so it is an in-distribution
     selection fold for the pretraining phase only.
  c. Calgary data never enters any ClarkNet evaluation block or normalizer fit, and
     ClarkNet test/deployment data never enters pretraining or fine-tuning.
Calgary transfers regime SHAPE (weekend factor, diurnal phase), not level (0.33 vs
45.7 counts/bucket, 84% zeros); whether pretraining helps is an empirical question
for the study, not this module.

WHAT THE DATA CANNOT SUPPORT (stated plainly)
---------------------------------------------
- No forward-only ClarkNet fold can train on a meaningful share of weekend: the only
  weekend inside any legal train region is Sat 00:00-03:50 (3.2% of fold b5's train).
  Weekend model behaviour on ClarkNet is therefore only ever an OOD measurement.
- Fold b6 cannot exist at all (replay window would enter training).
- The 7-day corpus yields exactly 3 selection folds and 1 OOD fold at 1-day blocks;
  smaller blocks would add folds whose eval blocks no longer contain a full diurnal
  cycle.
- Calgary's level and zero-inflation are so far from ClarkNet that pretraining can
  only be justified in per-region normalized space.

WHERE EACH THESIS NUMBER COMES FROM
-----------------------------------
- Closed-loop S3/S4 replay evidence: replay window [28,940, 29,020) inside the
  deployment test region [26243, 40315); never inside any training region.
- Model selection (hyperparameters, epoch budget, cell): blocked-CV selection folds
  b2/b3/b4, reported as mean +/- std (and min/max) across blocks.
- Extrapolation stress (weekend OOD): fold b5 and the deployment test region,
  reported separately with day-type composition; never aggregated into the selection
  mean.
- Pretraining (optional arm): Calgary pretrain region + Calgary weekend validation
  block only.
- Normalisation statistics: each spec's own train region (deployment arm: the
  amplified training portion, as served).
- "RPS" figures in circulation (45.70 -> 34.08) are 15 s bucket counts; true mean RPS
  is count/15 (3.05 -> 2.27); ratios and shifts are unit-invariant.

Run the dry run:  cd apps/experiment && uv run python -m experiment.tuning.splits
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

import numpy as np

# ── Frozen measured corpus facts (verified 2026-09-13 on the raw parquets) ────

SAMPLE_INTERVAL_SEC = 15
DAY = 5_760  # 15 s buckets per day

SEQUENCE_LENGTH = 30
HORIZON = 9
EMBARGO = SEQUENCE_LENGTH + HORIZON - 1  # 38 samples: formula minimum at every boundary

CLARKNET_ANCHOR = datetime(1995, 8, 28, 4, 0, 30, tzinfo=timezone.utc)
CLARKNET_N = 40_315
CLARKNET_SPAN_START = CLARKNET_ANCHOR
CLARKNET_SPAN_END = datetime(1995, 9, 4, 4, 0, 0, tzinfo=timezone.utc)

# Replay window 1995-09-02 04:35:30-04:55 UTC, frozen literal matching
# gru_probe.PROBE_REPLAY_WINDOW (a superset of the stated 04:55:00 end by 2 buckets).
REPLAY_WINDOW = (28_940, 29_020)

# Frozen deployment protocol (kept for closed-loop comparability; see rationale §1).
DEPLOYMENT_TRAIN = (0, 22_500)
DEPLOYMENT_VAL = (22_539, 26_205)
DEPLOYMENT_TEST = (26_243, 40_315)

CALGARY_ANCHOR = datetime(1994, 10, 24, 19, 41, 30, tzinfo=timezone.utc)

CALGARY_N = 2_027_652
CALGARY_PRETRAIN_CUT = datetime(1995, 8, 28, 0, 0, 0, tzinfo=timezone.utc)  # idx 1,769,354
CALGARY_PRETRAIN_VALID_DAYS = 2  # the cut-adjacent Sat+Sun block
_CORPUS_SIZES = {"clarknet": CLARKNET_N, "calgary": CALGARY_N}

# Role/selection decision thresholds (rationale §2-3).
SELECTION_MAX_EVAL_WEEKEND_SHARE = 0.5  # eval majority regime must be weekday...
SELECTION_MIN_TRAIN_REGIME_SHARE = 0.10  # ...unless train holds >=10% of that regime
DAY_SHARE_EPS = 0.01  # a day type "present" in a region at >=1% of its buckets

DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
ROLES = ("selection", "ood_report", "deployment")

_CITATIONS = (
    "Hyndman & Athanasopoulos, fpp3 ch. 5 (tscv.html, rolling-origin evaluation); "
    "Bergmeir & Benitez 2012, Information Sciences 191:192-213; Tashman 2000, "
    "Int. J. Forecasting 16(4):437-450"
)


# ── Core records ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class IndexRange:
    """Half-open [start, stop) index range into a 15 s bucket series."""

    start: int
    stop: int

    def __len__(self) -> int:
        return self.stop - self.start

    def __contains__(self, index: int) -> bool:
        return self.start <= index < self.stop

    def span(self, anchor: datetime, step: int = SAMPLE_INTERVAL_SEC) -> tuple[datetime, datetime]:
        return (
            anchor + timedelta(seconds=self.start * step),
            anchor + timedelta(seconds=(self.stop - 1) * step),
        )


@dataclass(frozen=True)
class RegionProfile:
    """Day-type composition of one region, by calendar day of bucket start (UTC)."""

    day_shares: Mapping[str, float]  # day name -> share of the region's buckets
    weekend_share: float
    days: frozenset[str] = field(default_factory=frozenset)  # share >= DAY_SHARE_EPS


@dataclass(frozen=True)
class NormalizerStats:
    """Robust statistics of one training region, fitted on transformed values."""

    center: float
    scale: float
    method: str
    transform: str
    fit_range: IndexRange
    n_fit: int


@dataclass(frozen=True)
class SplitSpec:
    """One train/eval split with its measured composition and design provenance.

    ``train``/``validation``/``test`` are half-open index ranges into the corpus
    series (15 s buckets). ``embargo`` is the enforced minimum gap in samples
    between the end of every training region and the start of every evaluation
    region. ``profiles`` records the day-type composition of every present region;
    ``rationale`` records the source of the design decision; ``used_for_selection``
    is False for OOD/deployment blocks, enforced by ``validate``.
    """

    name: str
    corpus: str
    role: str  # ROLES
    eval_of_record: str  # which region produces the reported number
    train: IndexRange | None
    validation: IndexRange | None
    test: IndexRange | None
    embargo: int
    profiles: Mapping[str, RegionProfile]
    rationale: str
    used_for_selection: bool
    region_means: Mapping[str, float] | None = None  # counts/bucket, if values given
    level_shift: float | None = None  # eval_of_record mean / train mean
    notes: tuple[str, ...] = ()

    def region(self, name: str) -> IndexRange | None:
        return {"train": self.train, "validation": self.validation, "test": self.test}[name]

    def require_region(self, name: str) -> IndexRange:
        """Return a region that must be present, raising when the design omits it.

        ``region`` returns ``None`` for an absent region because some designs
        legitimately omit one — a fold with no validation tail, a deployment
        split with no separate test. Callers that assume presence use this, so
        the assumption is checked in one place instead of asserted at each use.
        """
        rng = self.region(name)
        if rng is None:
            raise ValueError(f"{self.name}: region {name!r} is not present ({self.present_regions()})")
        return rng

    def present_regions(self) -> tuple[str, ...]:
        return tuple(n for n in ("train", "validation", "test") if self.region(n) is not None)

    def validate(self, n_total: int = CLARKNET_N, anchor: datetime | None = None) -> "SplitSpec":
        anchor = anchor or (CLARKNET_ANCHOR if self.corpus == "clarknet" else CALGARY_ANCHOR)
        assert self.role in ROLES, f"{self.name}: unknown role {self.role!r}; expected one of {ROLES}"
        assert self.eval_of_record in self.present_regions(), (
            f"{self.name}: eval_of_record {self.eval_of_record!r} is not a present region ({self.present_regions()})"
        )
        assert self.used_for_selection == (self.role == "selection"), (
            f"{self.name}: role={self.role!r} but used_for_selection={self.used_for_selection}; "
            "only selection folds may drive model choice (rationale 1/3)"
        )
        for name in self.present_regions():
            rng = self.region(name)
            assert rng is not None and 0 <= rng.start < rng.stop <= n_total, (
                f"{self.name}: region {name!r} [{rng.start if rng else '?'}, "
                f"{rng.stop if rng else '?'}) outside corpus [0, {n_total})"
            )
            assert name in self.profiles, f"{self.name}: day-type composition not recorded for region {name!r}"
        ordered = [self.require_region(n) for n in self.present_regions()]
        for earlier, later in zip(ordered, ordered[1:]):
            assert earlier.stop <= later.start, (
                f"{self.name}: regions overlap or are out of order at {earlier.stop} > {later.start}"
            )
        assert_no_leakage(self, n_total)
        assert_replay_placement(self)
        if self.role == "selection":
            assert_day_type_overlap(self)
        return self


@dataclass(frozen=True)
class BlockedCVPlan:
    """Blocked-CV folds plus blocks skipped for a recorded, asserted reason."""

    specs: tuple[SplitSpec, ...]
    skipped: tuple[Mapping[str, Any], ...]

    def selection_folds(self) -> tuple[SplitSpec, ...]:
        return tuple(s for s in self.specs if s.role == "selection")

    def ood_folds(self) -> tuple[SplitSpec, ...]:
        return tuple(s for s in self.specs if s.role == "ood_report")


# ── Day-type arithmetic (stdlib only, O(#days) not O(#buckets)) ──────────────


def _iter_day_segments(anchor: datetime, start: int, stop: int, step: int) -> Iterator[tuple[int, int]]:
    """Yield (weekday, bucket_count) for each calendar-day run in [start, stop)."""
    i = start
    while i < stop:
        ts = anchor + timedelta(seconds=i * step)
        next_midnight = datetime(ts.year, ts.month, ts.day, tzinfo=ts.tzinfo) + timedelta(days=1)
        j = math.ceil((next_midnight - anchor).total_seconds() / step)
        j = min(max(j, i + 1), stop)
        yield ts.weekday(), j - i
        i = j


def region_profile(anchor: datetime, start: int, stop: int, step: int = SAMPLE_INTERVAL_SEC) -> RegionProfile:
    """Day-type composition of [start, stop): per-day shares and weekend share."""
    counts = [0] * 7
    total = stop - start
    assert total > 0, f"region_profile on empty range [{start}, {stop})"
    for weekday, n in _iter_day_segments(anchor, start, stop, step):
        counts[weekday] += n
    shares = {DAY_NAMES[d]: counts[d] / total for d in range(7) if counts[d]}
    weekend = (counts[5] + counts[6]) / total
    days = frozenset(d for d, s in shares.items() if s >= DAY_SHARE_EPS)
    return RegionProfile(day_shares=shares, weekend_share=weekend, days=days)


def index_of(anchor: datetime, ts: datetime, step: int = SAMPLE_INTERVAL_SEC, n_total: int | None = None) -> int:
    """Exact bucket index of a timestamp on a gapless grid; loud if off-grid."""
    delta = (ts - anchor).total_seconds()
    q, r = divmod(delta, step)
    assert abs(r) < 1e-9, f"timestamp {ts} is off the {step}s grid anchored at {anchor}"
    idx = int(q)
    if n_total is not None:
        assert 0 <= idx < n_total, f"index {idx} of {ts} outside [0, {n_total})"
    return idx


# ── Loud assertions ──────────────────────────────────────────────────────────


def assert_no_leakage(spec: SplitSpec, n_total: int) -> None:
    """Training must end >= embargo samples before every evaluation block starts."""
    evals = [n for n in ("validation", "test") if spec.region(n) is not None]
    assert spec.train is not None or not evals, f"{spec.name}: no train region but eval regions {evals}"
    if spec.train is None:
        return
    for name in evals:
        rng = spec.region(name)
        assert rng is not None
        gap = rng.start - spec.require_region("train").stop
        assert gap >= spec.embargo, (
            f"{spec.name}: LEAKAGE - train ends at {spec.require_region('train').stop}, {name} starts at "
            f"{rng.start}, gap {gap} < embargo {spec.embargo} "
            f"(sequence_length {SEQUENCE_LENGTH} + horizon {HORIZON} - 1)"
        )


def assert_replay_placement(spec: SplitSpec) -> None:
    """The replay window [28940, 29020) never touches training; deployment holds it."""
    lo, hi = REPLAY_WINDOW
    if spec.corpus != "clarknet":
        return  # replay indices are ClarkNet-grid; other corpora are checked at construction
    if spec.train is not None:
        assert spec.require_region("train").stop <= lo or hi <= spec.require_region("train").start, (
            f"{spec.name}: LEAKAGE - replay window [{lo}, {hi}) "
            f"(1995-09-02 04:35:30-04:55 UTC) intersects train {spec.train}"
        )
    if spec.role == "deployment":
        held_out = [r for r in (spec.validation, spec.test) if r is not None]
        assert any(lo >= r.start and hi <= r.stop for r in held_out), (
            f"{spec.name}: replay window [{lo}, {hi}) must sit inside a held-out region, got {[r for r in held_out]}"
        )


def assert_day_type_overlap(spec: SplitSpec) -> None:
    """A selection fold must evaluate a regime its training region actually saw."""
    assert spec.train is not None and spec.validation is not None, (
        f"{spec.name}: selection fold needs train and validation regions"
    )
    train_prof = spec.profiles["train"]
    eval_prof = spec.profiles[spec.eval_of_record] if spec.eval_of_record != "train" else spec.profiles["validation"]
    overlap = train_prof.days & eval_prof.days
    assert overlap, (
        f"{spec.name}: EMPTY DAY-TYPE OVERLAP - train days {sorted(train_prof.days)} vs eval days "
        f"{sorted(eval_prof.days)}; selecting on this fold selects an extrapolator, not a "
        "predictor (Bergmeir & Benitez 2012; rationale 3)"
    )
    majority_weekend = eval_prof.weekend_share >= SELECTION_MAX_EVAL_WEEKEND_SHARE
    if majority_weekend:
        assert train_prof.weekend_share >= SELECTION_MIN_TRAIN_REGIME_SHARE, (
            f"{spec.name}: eval block is {eval_prof.weekend_share:.1%} weekend but train holds only "
            f"{train_prof.weekend_share:.1%} weekend (< {SELECTION_MIN_TRAIN_REGIME_SHARE:.0%}); "
            "this is an OOD block, mark it role='ood_report' (rationale 3)"
        )


# ── Constructors ─────────────────────────────────────────────────────────────


def _attach_values(
    spec: SplitSpec,
    values: np.ndarray | None,
    anchor: datetime,
    n_total: int,
) -> SplitSpec:
    """Record per-region means (counts/bucket) and the train->eval level shift."""
    if values is None:
        return spec
    assert len(values) == n_total, f"values length {len(values)} != corpus size {n_total}"
    means = {
        name: float(np.mean(values[spec.require_region(name).start : spec.require_region(name).stop]))
        for name in spec.present_regions()
    }
    shift = None
    if spec.train is not None:
        eval_rng = spec.region(spec.eval_of_record)
        assert eval_rng is not None
        shift = means[spec.eval_of_record] / means["train"] if means["train"] else float("nan")
    return replace(spec, region_means=means, level_shift=shift)


def deployment_split(
    values: np.ndarray | None = None,
    n_total: int = CLARKNET_N,
    anchor: datetime = CLARKNET_ANCHOR,
) -> SplitSpec:
    """The frozen deployment evaluation: forward held-out, OOD, never for selection.

    Kept region-for-region identical to the inherited protocol so the in-flight
    closed-loop evidence stays comparable; what changes is its role (rationale 1).
    """
    tr, va, te = (IndexRange(a, b) for a, b in (DEPLOYMENT_TRAIN, DEPLOYMENT_VAL, DEPLOYMENT_TEST))
    profiles = {
        "train": region_profile(anchor, tr.start, tr.stop),
        "validation": region_profile(anchor, va.start, va.stop),
        "test": region_profile(anchor, te.start, te.stop),
    }
    spec = SplitSpec(
        name="clarknet-deployment-frozen",
        corpus="clarknet",
        role="deployment",
        eval_of_record="test",
        train=tr,
        validation=va,
        test=te,
        embargo=EMBARGO,
        profiles=profiles,
        rationale=(
            "Frozen closed-loop region kept for replay-window placement and Tashman-2000 "
            "deployment fidelity; test is 81.86% weekend (level shift 0.746 vs train), "
            "reported separately with composition and excluded from selection. " + _CITATIONS
        ),
        used_for_selection=False,
        notes=(
            f"train->val gap {va.start - tr.stop} samples, val->test gap {te.start - va.stop} samples "
            f"(both >= embargo {EMBARGO})",
        ),
    )
    spec = _attach_values(spec, values, anchor, n_total)
    return spec.validate(n_total, anchor)


def blocked_cv(
    values: np.ndarray | None = None,
    n_total: int = CLARKNET_N,
    anchor: datetime = CLARKNET_ANCHOR,
    embargo: int = EMBARGO,
    block_days: int = 1,
    min_train_days: int = 2,
) -> BlockedCVPlan:
    """Expanding-origin blocked CV: 1-day blocks, train = all prior data minus embargo.

    Folds whose eval block's day types are unseen in train (or whose majority regime
    is <10% of train) are emitted as role='ood_report' instead of selection folds.
    Blocks whose train region would contain the replay window are skipped with a
    recorded reason (rationale 2).
    """
    block = block_days * DAY
    first = min_train_days  # block index of the first legal fold
    specs: list[SplitSpec] = []
    skipped: list[Mapping[str, Any]] = []
    for b in range(first, math.ceil(n_total / block)):
        eval_start, eval_stop = b * block, min((b + 1) * block, n_total)
        train = IndexRange(0, eval_start - embargo)
        if REPLAY_WINDOW[0] < train.stop:  # replay window inside the fold's train
            skipped.append(
                {
                    "block": b,
                    "eval": (eval_start, eval_stop),
                    "reason": (
                        f"train [0, {train.stop}) would contain the replay window "
                        f"{REPLAY_WINDOW}; forbidden by the replay-placement rule"
                    ),
                }
            )
            continue
        profiles = {
            "train": region_profile(anchor, train.start, train.stop),
            "validation": region_profile(anchor, eval_start, eval_stop),
        }
        train_days = profiles["train"].days
        eval_days = profiles["validation"].days
        eval_wk = profiles["validation"].weekend_share
        train_wk = profiles["train"].weekend_share
        overlap = bool(train_days & eval_days)
        regime_ok = eval_wk < SELECTION_MAX_EVAL_WEEKEND_SHARE or train_wk >= SELECTION_MIN_TRAIN_REGIME_SHARE
        is_selection = overlap and regime_ok
        spec = SplitSpec(
            name=f"clarknet-bcv-b{b}",
            corpus="clarknet",
            role="selection" if is_selection else "ood_report",
            eval_of_record="validation",
            train=train,
            validation=IndexRange(eval_start, eval_stop),
            test=None,
            embargo=embargo,
            profiles=profiles,
            rationale=(
                (
                    "1-day blocked CV fold, expanding origin (Bergmeir & Benitez 2012; fpp3 ch. 5). "
                    f"Selection fold: day-type overlap {sorted(train_days & eval_days)}, eval weekend "
                    f"{eval_wk:.1%}, train weekend {train_wk:.1%}. " + _CITATIONS
                )
                if is_selection
                else (
                    "1-day blocked CV fold, expanding origin, but eval regime is out of training "
                    f"distribution (eval weekend {eval_wk:.1%}, train weekend {train_wk:.1%}, overlap "
                    f"{sorted(train_days & eval_days)}); quarantined from selection as the weekend "
                    "extrapolation rehearsal (rationale 3). " + _CITATIONS
                )
            ),
            used_for_selection=is_selection,
            notes=(f"train->eval gap {eval_start - train.stop} samples == embargo {embargo}",),
        )
        spec = _attach_values(spec, values, anchor, n_total)
        specs.append(spec.validate(n_total, anchor))
    assert len(specs) >= 2, (
        f"blocked_cv produced {len(specs)} folds on n_total={n_total}; the protocol needs "
        ">=2 folds for a mean/spread aggregate"
    )
    assert any(s.role == "selection" for s in specs), "blocked_cv produced no selection fold"
    return BlockedCVPlan(specs=tuple(specs), skipped=tuple(skipped))


def calgary_pretrain_split(
    values: np.ndarray | None = None,
    n_total: int = CALGARY_N,
    anchor: datetime = CALGARY_ANCHOR,
    embargo: int = EMBARGO,
) -> SplitSpec:
    """Calgary pretraining region plus its pure-weekend validation block.

    Train [0, cut - 2*DAY - embargo), validation [cut - 2*DAY, cut) where cut is the
    index of 1995-08-28 00:00 UTC (1,769,354): the last Calgary block before the
    ClarkNet span is Sat+Sun 1995-08-26/27. Everything at or after the cut is unused,
    which excludes the Calgary buckets overlapping the ClarkNet week ([1,770,316,
    1,810,634)) plus a 4-hour guard band (rationale 5).
    """
    cut = index_of(anchor, CALGARY_PRETRAIN_CUT, n_total=n_total)
    valid_len = CALGARY_PRETRAIN_VALID_DAYS * DAY
    train = IndexRange(0, cut - valid_len - embargo)
    valid = IndexRange(cut - valid_len, cut)
    train_end_ts = anchor + timedelta(seconds=train.stop * SAMPLE_INTERVAL_SEC)
    assert train_end_ts < CLARKNET_SPAN_START, (
        f"Calgary pretrain region ends {train_end_ts}, must precede the ClarkNet span "
        f"start {CLARKNET_SPAN_START} (leak rule 5a)"
    )
    profiles = {
        "train": region_profile(anchor, train.start, train.stop),
        "validation": region_profile(anchor, valid.start, valid.stop),
    }
    assert profiles["validation"].weekend_share == 1.0, (
        "Calgary pretrain validation block must be the pure-weekend Sat+Sun block; got "
        f"weekend share {profiles['validation'].weekend_share:.3f}"
    )
    assert profiles["train"].weekend_share >= SELECTION_MIN_TRAIN_REGIME_SHARE, (
        "Calgary pretrain train region lost its weekend coverage "
        f"({profiles['train'].weekend_share:.3f}); cannot supply the missing regime"
    )
    spec = SplitSpec(
        name="calgary-pretrain",
        corpus="calgary",
        role="selection",
        eval_of_record="validation",
        train=train,
        validation=valid,
        test=None,
        embargo=embargo,
        profiles=profiles,
        rationale=(
            "Calgary pretraining supplies the weekend regime ClarkNet cannot (44 full "
            f"weekends in train, weekend share {profiles['train'].weekend_share:.1%}); validation "
            "is the cut-adjacent pure Sat+Sun block, in-distribution for pretraining-phase "
            "selection only. Temporal overlap window with the ClarkNet week plus a 4 h guard "
            "band excluded; post-cut tail unused (rationale 5). " + _CITATIONS
        ),
        used_for_selection=True,
        notes=(
            f"cut index {cut} (1995-08-28 00:00 UTC); ClarkNet-overlap buckets "
            f"[{index_of(anchor, CLARKNET_SPAN_START)}, {index_of(anchor, CLARKNET_SPAN_END)}) never used",
            "Calgary data never enters any ClarkNet eval block or normalizer fit",
        ),
    )
    spec = _attach_values(spec, values, anchor, n_total)
    return spec.validate(n_total, anchor)


# ── Normalisation (rationale 4) ──────────────────────────────────────────────


def normalizer_stats(
    values: np.ndarray,
    spec: SplitSpec,
    region: str = "train",
    transform: str = "log1p",
) -> NormalizerStats:
    """Fit robust stats for ``spec`` on its TRAIN region only; any other region raises."""
    assert region == "train", (
        f"normalizer_stats refuses to fit on region {region!r}: statistics are fitted on the "
        "training region only (leak rule, rationale 4)"
    )
    assert spec.train is not None, f"{spec.name}: no train region to fit"
    fit = np.asarray(values[spec.require_region("train").start : spec.require_region("train").stop], dtype=np.float64)
    x = np.log1p(fit) if transform == "log1p" else fit.copy()
    center = float(np.median(x))
    iqr = float(np.percentile(x, 75) - np.percentile(x, 25))
    scale = iqr if iqr > 1e-12 else float(x.std())
    assert scale > 1e-12, (
        f"{spec.name}: degenerate normalizer scale {scale:.3g} on train "
        f"[{spec.require_region('train').start}, {spec.require_region('train').stop}) - constant series cannot be normalized"
    )
    method = f"{transform}-median-iqr" if iqr > 1e-12 else f"{transform}-median-std-fallback"
    return NormalizerStats(
        center=center, scale=scale, method=method, transform=transform, fit_range=spec.train, n_fit=len(fit)
    )


def apply_normalizer(values: np.ndarray, stats: NormalizerStats) -> np.ndarray:
    x = (
        np.log1p(np.asarray(values, dtype=np.float64))
        if stats.transform == "log1p"
        else np.asarray(values, dtype=np.float64)
    )
    return (x - stats.center) / stats.scale


def invert_normalizer(normed: np.ndarray, stats: NormalizerStats) -> np.ndarray:
    x = np.asarray(normed, dtype=np.float64) * stats.scale + stats.center
    return np.expm1(x) if stats.transform == "log1p" else x


# ── Aggregation across blocks (rationale 2) ──────────────────────────────────


def aggregate_block_metrics(metrics: Mapping[str, float]) -> dict[str, float | int]:
    """Mean and spread across blocks; refuses a single-block 'aggregate'."""
    assert len(metrics) >= 2, (
        f"aggregate_block_metrics got {len(metrics)} block(s) {sorted(metrics)}: a mean/spread "
        "claim needs >=2 blocks - never report a single-block number as a CV aggregate"
    )
    vals = np.asarray(list(metrics.values()), dtype=np.float64)
    return {
        "mean": float(vals.mean()),
        "std": float(vals.std(ddof=1)),
        "min": float(vals.min()),
        "max": float(vals.max()),
        "n_blocks": int(vals.size),
    }


# ── Dry run (no training; loads parquets read-only) ──────────────────────────


def load_series(
    corpus: str,
    unit: str = "counts",
    scale_factor: float | None = None,
) -> np.ndarray:
    """Load a 15 s corpus series on the split grid; the one loader consumers import.

    ``unit='counts'`` returns requests per 15 s bucket (the EDA convention; the dry-run
    table and persistence references are in these units). ``unit='rps'`` returns the
    per-bucket mean RPS (``gru_study.load_clarknet_series`` convention = counts / 15).
    ``scale_factor`` multiplies after unit conversion (k6 replay amplitude 33.0 from
    ``data/trace-replay/clarknet_replay_manifest.json``; pass it for the deployment
    arm's normalizer fit, see rationale 4). Length is asserted against the frozen
    corpus size so index-grid mismatches fail loudly.
    """
    import pandas as pd  # lazy: core module stays pandas-free

    assert corpus in _CORPUS_SIZES, f"unknown corpus {corpus!r}; expected one of {sorted(_CORPUS_SIZES)}"
    assert unit in ("counts", "rps"), f"unknown unit {unit!r}; expected 'counts' or 'rps'"
    path = Path(__file__).resolve().parents[4] / "data" / "processed" / f"{corpus}_real_rps.parquet"
    df = pd.read_parquet(path)
    series = df[df.columns[0]].resample("15s").sum().dropna().astype(float)
    values = series.to_numpy(dtype=np.float64)
    assert len(values) == _CORPUS_SIZES[corpus], (
        f"{corpus}: loaded {len(values)} buckets, frozen corpus size is {_CORPUS_SIZES[corpus]}; "
        "the split indices are calibrated to the gapless grid - do not use them together"
    )
    if unit == "rps":
        values = values / SAMPLE_INTERVAL_SEC
    if scale_factor is not None:
        values = values * scale_factor
    return values


def _load_counts(corpus: str) -> np.ndarray:
    return load_series(corpus, unit="counts")


def _persistence_rmse(values: np.ndarray, start: int, stop: int, horizon: int = HORIZON) -> float:
    """RMSE of the persistence baseline on [start, stop) at the protocol horizon."""
    target = values[start + horizon : stop]
    pred = values[start : stop - horizon]
    return float(np.sqrt(np.mean((pred - target) ** 2)))


def _self_test() -> list[str]:
    """Deliberate-failure probes: each must raise AssertionError with numbers in it."""
    passed: list[str] = []
    leaky = SplitSpec(
        name="leaky-probe",
        corpus="clarknet",
        role="selection",
        eval_of_record="validation",
        train=IndexRange(0, 20_000),
        validation=IndexRange(20_010, 22_000),
        test=None,
        embargo=EMBARGO,
        profiles={
            "train": region_profile(CLARKNET_ANCHOR, 0, 20_000),
            "validation": region_profile(CLARKNET_ANCHOR, 20_010, 22_000),
        },
        rationale="probe",
        used_for_selection=True,
    )
    try:
        assert_no_leakage(leaky, CLARKNET_N)
    except AssertionError as e:
        assert "gap 10 < embargo 38" in str(e)
        passed.append("leakage probe (gap 10 < embargo 38)")
    replay_leak = replace(deployment_split(), train=IndexRange(0, 30_000))
    try:
        assert_replay_placement(replay_leak)
    except AssertionError as e:
        assert "replay window [28940, 29020)" in str(e)
        passed.append("replay-in-train probe")
    empty_overlap = SplitSpec(
        name="empty-overlap-probe",
        corpus="clarknet",
        role="selection",
        eval_of_record="validation",
        train=IndexRange(0, 22_500),
        validation=IndexRange(28_800, 34_560),
        test=None,
        embargo=EMBARGO,
        profiles={
            "train": region_profile(CLARKNET_ANCHOR, 0, 22_500),
            "validation": region_profile(CLARKNET_ANCHOR, 28_800, 34_560),
        },
        rationale="probe",
        used_for_selection=True,
    )
    try:
        assert_day_type_overlap(empty_overlap)
    except AssertionError as e:
        assert "EMPTY DAY-TYPE OVERLAP" in str(e)
        passed.append("empty day-type overlap probe (weekend eval, weekday train)")
    ck = np.full(CLARKNET_N, 7.0)
    try:
        normalizer_stats(ck, deployment_split())
    except AssertionError as e:
        assert "degenerate normalizer scale" in str(e)
        passed.append("degenerate-scale normalizer probe")
    try:
        normalizer_stats(ck, deployment_split(), region="validation")
    except AssertionError as e:
        assert "training region only" in str(e)
        passed.append("non-train normalizer-fit probe")
    try:
        aggregate_block_metrics({"b2": 1.0})
    except AssertionError as e:
        assert "never report a single-block number" in str(e)
        passed.append("single-block aggregate probe")
    return passed


def dry_run() -> int:
    ck = _load_counts("clarknet")
    cg = _load_counts("calgary")
    dep = deployment_split(ck)
    plan = blocked_cv(ck)
    pre = calgary_pretrain_split(cg)

    header = (
        f"{'spec':24} {'role':11} {'region':10} {'index range':17} {'n':>7} "
        f"{'span (UTC)':45} {'day types (share)':34} {'wknd':>6} {'mean/15s':>9} {'RPS':>7} {'shift':>6}"
    )
    lines = [
        "CLARKNET DEPLOYMENT + BLOCKED CV + CALGARY PRETRAIN - dry run "
        f"(embargo {EMBARGO} = {SEQUENCE_LENGTH}+{HORIZON}-1)",
        "",
        header,
        "-" * len(header),
    ]
    import hashlib

    sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    lines += [
        f"splits.py sha256 {sha}",
        "series path: <corpus>_real_rps.parquet -> resample('15s').sum() -> counts/15s bucket "
        "(RPS = counts/15; gru_study per-bucket-mean convention = unit='rps' in load_series)",
        "deployment arm at served amplitude = counts x 33.0 (clarknet_replay_manifest.json) "
        "before normalizer_stats; split geometry unchanged",
        "",
    ]

    def row(spec: SplitSpec, anchor: datetime) -> None:
        for name in spec.present_regions():
            rng = spec.region(name)
            assert rng is not None
            prof = spec.profiles[name]
            lo_ts, hi_ts = rng.span(anchor)
            days = ",".join(
                f"{d}({prof.day_shares[d]:.0%})"
                for d in DAY_NAMES
                if d in prof.day_shares and prof.day_shares[d] >= 0.01
            )
            mean = spec.region_means[name] if spec.region_means else float("nan")
            shift = spec.level_shift if name == spec.eval_of_record else float("nan")
            lines.append(
                f"{spec.name:24} {spec.role:11} {name:10} [{rng.start:6},{rng.stop:6}) {len(rng):7} "
                f"{str(lo_ts)[:16]}..{str(hi_ts)[11:16]:13} {days:34} {prof.weekend_share:6.1%} "
                f"{mean:9.3f} {mean / 15:7.3f} {shift:6.3f}"
            )

    row(dep, CLARKNET_ANCHOR)
    for s in plan.specs:
        row(s, CLARKNET_ANCHOR)
    row(pre, CALGARY_ANCHOR)
    for sk in plan.skipped:
        lines.append(f"{'SKIPPED block b' + str(sk['block']):24} {'skipped':11} eval={sk['eval']} - {sk['reason']}")
    lines.append("")
    lines.append(
        f"replay window {REPLAY_WINDOW} (Sat 1995-09-02 04:35:30-04:55 UTC): inside deployment test "
        f"[{DEPLOYMENT_TEST[0]},{DEPLOYMENT_TEST[1]}); disjoint from every train region above"
    )
    lines.append("")

    per_fold = {
        s.name: _persistence_rmse(ck, s.require_region("validation").start, s.require_region("validation").stop)
        for s in plan.specs
        if s.validation
    }
    sel = {s.name: per_fold[s.name] for s in plan.selection_folds()}
    agg = aggregate_block_metrics(sel)
    lines.append(
        "aggregation demo - persistence RMSE (counts/15s) at horizon 9, mean +/- std across "
        f"SELECTION folds {sorted(sel)}: {agg['mean']:.3f} +/- {agg['std']:.3f} "
        f"(min {agg['min']:.3f}, max {agg['max']:.3f}, n={agg['n_blocks']});"
    )
    lines.append(
        "OOD folds reported separately, never in the selection aggregate: "
        + ", ".join(f"{s.name}={per_fold[s.name]:.3f}" for s in plan.ood_folds())
        + f"; deployment persistence RMSE={_persistence_rmse(ck, DEPLOYMENT_TEST[0], DEPLOYMENT_TEST[1]):.3f}"
    )
    lines.append("")
    n_stats = normalizer_stats(ck, dep)
    c_stats = normalizer_stats(cg, pre)
    lines.append(
        f"normalizers: deployment arm {n_stats.method} (center {n_stats.center:.4f}, scale "
        f"{n_stats.scale:.4f}, n={n_stats.n_fit}); calgary pretrain {c_stats.method} "
        f"(center {c_stats.center:.4f}, scale {c_stats.scale:.4f}, n={c_stats.n_fit} - IQR fallback engaged)"
    )
    lines.append("")
    probes = _self_test()
    lines.append(f"self-test: {len(probes)}/6 deliberate-failure probes raised the expected AssertionError:")
    for p in probes:
        lines.append(f"  PASS {p}")
    lines.append("")
    lines += [
        "THESIS NUMBER PROVENANCE",
        "  closed-loop S3/S4 replay evidence : replay window inside deployment test "
        f"{DEPLOYMENT_TEST}; never in any training region",
        "  model selection (hparams/epochs)  : blocked-CV selection folds "
        + ", ".join(s.name for s in plan.selection_folds())
        + " (mean +/- std, never a single number)",
        "  weekend extrapolation stress      : "
        + ", ".join(s.name for s in plan.ood_folds())
        + " and the deployment test region, reported separately with day-type composition",
        "  pretraining arm (optional)        : calgary-pretrain train + Sat+Sun validation block only",
        "  normalisation statistics          : each spec's own train region (deployment: amplified series)",
        "LIMITS (data cannot support): no forward-only ClarkNet fold trains on meaningful weekend "
        "(max 3.2% pre-dawn Sat in fold b5); fold b6 unusable (replay in train); only 3 selection "
        "folds exist; Calgary level 0.33 vs 45.7 counts/bucket with 84% zeros - shape transfer only.",
    ]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(dry_run())

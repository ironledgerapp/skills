"""Load maths for the program designer: every number a draft shows comes from here (G-6).

Rules implemented (references/):
  rulebook.md         L-1 to L-11 (e1RM, TM, wave, warm-up, deload, TM moves),
                      L-14 (FSL), F-5 (plate-loadable), F-11 (lb), W-1 (benchmark ladder)
  client-types.md     CT-PLM-1 (top-set range), CT-PLM-4 (back-downs),
                      CT-PLM-5 (top-set RPE), CT-PLM-13 (accessory RIR), CT-PLM-20 (RPE as RIR)
  ironledger-import   IL-17 (warm-up note)

Two e1RMs live here and are never mixed:
  e1rm         the programming e1RM (L-1, L-2): Epley 0.0333, a single is the weight, CEILING to the step
  e1rm_parity  IronLedger's display e1RM: whole-number Epley, rounded half up like Math.round

Floats: loads are floats compared with a 1e-9 tolerance. round_up never lets float noise
(107.50000000000001) push a load up a whole step, and products of a load and a percentage go
through Decimal so 107.5 x 0.65 is exactly 69.875.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from lib import library, model
from lib.checks import Check, where

TOL = 1e-9
EPLEY = Decimal("0.0333")          # L-1
CAP = 10                           # offending rows listed per rule before a summary line

UNITS = ("kg", "lb")
BAR = {"kg": 20.0, "lb": 45.0}                 # F-5, F-11
STEP = {"kg": 2.5, "lb": 5.0}                  # L-4 {M2}, F-11
MICRO_STEP = {"kg": 1.25, "lb": 2.5}           # L-4 microplates, F-11
INCREMENT = {"kg": {"lower": 5.0, "upper": 2.5},      # L-9 {M7}
             "lb": {"lower": 10.0, "upper": 5.0}}     # F-11
TOPSET_WIDTH = {"kg": {"lower": 10.0, "upper": 5.0},  # CT-PLM-1
                "lb": {"lower": 20.0, "upper": 10.0}}  # F-11
KG_TO_LB = Decimal("2.2046")                   # F-11

# A lift's side for TM increments (L-9). Extend here; names that contain "squat" or
# "deadlift" are treated as lower body too, so a variant never silently gets +2.5 kg.
LOWER = {
    "Squat", "Back Squat", "High Bar Squat", "Low Bar Squat", "Front Squat", "Pause Squat",
    "Tempo Squat", "Box Squat", "Safety Bar Squat",
    "Deadlift", "Conventional Deadlift", "Sumo Deadlift", "Deficit Deadlift", "Block Pull",
    "Rack Pull",
}

# L-5: week -> ((fraction of TM, reps), ...); the last set is the AMRAP.
WAVE = {
    1: ((0.65, "5"), (0.75, "5"), (0.85, "5+")),
    2: ((0.70, "3"), (0.80, "3"), (0.90, "3+")),
    3: ((0.75, "5"), (0.85, "3"), (0.95, "1+")),
}
WARMUP = ((0.40, 5), (0.50, 5), (0.60, 3))                                # L-6 {M5}: after bar x 20
BENCHMARK = ((0.40, 6), (0.50, 4), (0.65, 2), (0.70, 2), (0.80, 1))       # W-1: after bar x 20

WAVE_ROLES = ("main", "main_amrap")
COMPUTED_ROLES = ("main", "main_amrap", "topset", "backdown", "supplemental", "single", "benchmark")
assert set(COMPUTED_ROLES) <= set(model.ROLES)


# --- units, steps, rounding ---------------------------------------------------------

def _unit(unit) -> str:
    u = str(unit or "").strip().lower()
    if u not in UNITS:
        raise ValueError(f"unit must be 'kg' or 'lb', got {unit!r} (F-10)")
    return u


def bar_weight(unit) -> float:
    """The empty bar: 20 kg or 45 lb (F-5, F-11)."""
    return BAR[_unit(unit)]


def step_for(unit, microplates: bool = False) -> float:
    """The load step: 2.5 kg (1.25 with microplates), 5 lb (2.5 with microplates) (L-4, F-11)."""
    u = _unit(unit)
    return MICRO_STEP[u] if microplates else STEP[u]


def round_up(x, step) -> float:
    """CEILING x to a multiple of step, float-safe (L-4): 107.5 stays 107.5, 105.75 goes to 107.5."""
    step = float(step)
    if step <= 0:
        raise ValueError(f"step must be positive, got {step}")
    n = math.ceil(float(x) / step - TOL)
    return round(n * step, 4) + 0.0  # + 0.0 turns -0.0 into 0.0


def _mul(a, b) -> float:
    """a x b computed exactly in decimal, then back to float (107.5 x 0.65 = 69.875)."""
    return float(Decimal(repr(float(a))) * Decimal(repr(float(b))))


def _is_multiple(x: float, step: float) -> bool:
    return abs(x - round(x / step) * step) <= TOL


def is_plate_loadable(load, unit, microplates: bool = False) -> bool:
    """A multiple of the step and at least the empty bar (F-5)."""
    x = _num(load)
    if x is None:
        return False
    return x >= bar_weight(unit) - TOL and _is_multiple(x, step_for(unit, microplates))


def convert_kg(kg, unit, microplates: bool = False) -> float:
    """A kg figure in the lifter's unit: lb at 2.2046, then CEILING to the lb step (F-11)."""
    u = _unit(unit)
    if u == "kg":
        return round_up(kg, step_for(u, microplates))
    return round_up(float(Decimal(repr(float(kg))) * KG_TO_LB), step_for(u, microplates))


def _fmt(x) -> str:
    """107.5 -> '107.5', 45.0 -> '45', 81.25 -> '81.25'."""
    s = f"{float(x):.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _num(v) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return None if math.isnan(v) else float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except ValueError:
            return None
    return None


# --- e1RM and TM -----------------------------------------------------------------------

def _whole(reps, what="reps") -> int:
    if isinstance(reps, bool) or not float(reps).is_integer():
        raise ValueError(f"{what} must be a whole number, got {reps!r}")
    return int(reps)


def e1rm(weight, reps, step) -> float:
    """Programming e1RM (L-1, L-2 {M6}): weight x reps x 0.0333 + weight, CEILING to the step.

    A single is the weight itself, with no 0.0333 inflation (L-2); it still rounds up to the
    step, which is a no-op for any plate-loadable weight. Sets above 10 reps are refused:
    L-2 caps a benchmark at 10 and L-12 keeps TM and e1RM updates to 10 reps or fewer.
    """
    w = float(weight)
    r = _whole(reps)
    if w <= 0:
        raise ValueError(f"weight must be positive, got {weight!r}")
    if r < 1 or r > 10:
        raise ValueError(f"an e1RM needs 1 to 10 reps (L-2, L-12), got {r}")
    if r == 1:
        return round_up(w, step)
    raw = Decimal(repr(w)) * r * EPLEY + Decimal(repr(w))
    return round_up(float(raw), step)


def e1rm_parity(weight, reps):
    """IronLedger's estimate1RM, for matching what the lifter sees (AN-1). Never for programming (AN-2).

    0 when weight or reps is 0 or less; the weight itself at 1 rep; otherwise
    Math.round(weight * (1 + reps / 30)), ported as floor(x + 0.5), never Python's round().
    AN-1 wins over the contract's "int" where they differ: at 1 rep the app shows the weight
    itself, so 102.5 x 1 is 102.5. Whole weights come back as int.
    """
    w = float(weight)
    if w <= 0 or reps <= 0:
        return 0
    if reps == 1:
        return int(w) if w.is_integer() else w
    return int(math.floor(w * (1 + reps / 30) + 0.5))


def training_max(e1rm, pct, step) -> float:
    """TM = e1RM x pct, CEILING to the step (L-3 {M7}). pct is 0.90, or 0.85 for novice,
    returning or uncertain-benchmark lifters; anything else is refused."""
    p = float(pct)
    if not any(abs(p - ok) < TOL for ok in (0.90, 0.85)):
        raise ValueError(f"TM percentage must be 0.90 or 0.85 (L-3), got {pct!r}")
    return round_up(_mul(e1rm, p), step)


# --- the wave, warm-up, FSL, deload, benchmark ------------------------------------------

def wave531(tm, week, step) -> list[tuple[float, str, float]]:
    """[(pct, reps, load)] for weeks 1-3 (L-5); the last set is the AMRAP ("5+", "3+", "1+").

    Loads are CEILING to the step and are not clamped to the bar: a work set under the bar is
    flagged under F-5, never quietly changed. Week 4 is the deload (L-7): warm-up only.
    """
    if week not in WAVE:
        raise ValueError(f"wave531 covers weeks 1-3; week 4 is the deload, warm-up only (L-7), got {week!r}")
    return [(pct, reps, round_up(_mul(tm, pct), step)) for pct, reps in WAVE[week]]


def warmup531(tm, step, unit) -> list[tuple[str, int, float]]:
    """[(label, reps, load)]: bar x 20, then 40/50/60% TM x 5/5/3 (L-6 {M5}).
    A load that would fall below the empty bar is the bar (F-5). The L-7 deload keeps only this."""
    bar = bar_weight(unit)
    out = [("Bar", 20, bar)]
    for pct, reps in WARMUP:
        out.append((f"{round(pct * 100)}%", reps, max(bar, round_up(_mul(tm, pct), step))))
    return out


def warmup_note(tm, step, unit) -> str:
    """The IL-17 compact warm-up, e.g. 'Warm-up bar x20, 45x5, 55x5, 65x3'.

    A warm-up clamped to the bar prints as the bar's number (20 or 45), not 'bar': F-5 writes
    the bar as `20` in the import, and this string lives in the import's Notes. The opening 'bar x20' is IL-17's own fixed wording.
    """
    parts = [f"{_fmt(load)}x{reps}" for _, reps, load in warmup531(tm, step, unit)[1:]]
    return "Warm-up bar x20, " + ", ".join(parts)


def fsl(tm, week, step, sets: int = 5) -> tuple[float, str, float, int]:
    """First Set Last (L-14 {M3}): (pct, "5", load, sets), 3 to 5 sets x 5 at the week's first work-set %."""
    if week not in WAVE:
        raise ValueError(f"FSL follows a loading week 1-3, got {week!r}")
    if _whole(sets, "sets") not in (3, 4, 5):
        raise ValueError(f"FSL is 3 to 5 sets (L-14), got {sets!r}")
    pct = WAVE[week][0][0]
    return (pct, "5", round_up(_mul(tm, pct), step), int(sets))


def deload_accessory(sets, rir) -> tuple[int, str]:
    """An accessory in the L-7 {M4} deload: the same exercise with 30 to 50% fewer sets, RIR +1, at least 3.

    The cut is ceil(30% of sets), which always lands inside 30-50% for 2 or more sets
    (3 -> 2, 4 -> 2, 5 -> 3); a single set stays a single set. RIR keeps its shape:
    '2' -> '3', '2-3' -> '3-4', '0-1' -> '3', a per-set list shifts entry by entry.
    """
    n = _whole(sets, "sets")
    if n < 1:
        raise ValueError(f"sets must be 1 or more, got {sets!r}")
    kept = max(1, n - math.ceil(n * 0.3 - TOL))
    entries = [e.strip() for e in str(rir).split(",")]
    out = []
    for e in entries:
        m = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", e)
        if not m:
            raise ValueError(f"RIR {rir!r} is not '2', '1-2' or '2, 2, 1' (IL-12)")
        lo = max(int(m.group(1)) + 1, 3)
        hi = max(int(m.group(2)) + 1, 3) if m.group(2) else lo
        out.append(str(lo) if lo == hi else f"{lo}-{hi}")
    if len(out) > 1:
        out = (out + [out[-1]] * kept)[:kept]
    return kept, ", ".join(out)


def benchmark_ladder(e1rm_est, step, unit) -> list[tuple[str, int, float]]:
    """The W-1 benchmark session ramp for a lift with no measured number (W-1, W-5).

    [(label, reps, load)]: bar x 20, then 40% x 6, 50% x 4, 65% x 2, 70% x 2 and 80% x 1 of the
    estimated e1RM, below-bar loads becoming the bar (F-5). The benchmark set that follows,
    one set of 3 to 5 at RIR 1 to 2 (RIR 3 for novices and returning lifters), is the
    lifter's own load, so it is not returned; weeks 2 onward come from its result (W-5).
    """
    bar = bar_weight(unit)
    out = [("Bar", 20, bar)]
    for pct, reps in BENCHMARK:
        out.append((f"{round(pct * 100)}%", reps, max(bar, round_up(_mul(e1rm_est, pct), step))))
    return out


# --- topset-backdown (CT-PLM) -------------------------------------------------------------

def is_lower(lift: str) -> bool:
    n = str(lift or "")
    return n in LOWER or "squat" in n.lower() or "deadlift" in n.lower()


def topset_range(mid, lift, unit) -> tuple[float, float]:
    """(low, high) of a top-set load range centred on mid (CT-PLM-1 {M10}).

    10 kg wide for squat and deadlift, 5 kg for bench; 20 lb and 10 lb for an lb lifter (F-11).
    The midpoint is first CEILING to the unit's standard step, so both ends stay plate-loadable.
    CT-PLM-1 names only the competition lifts; any other upper-body lift takes the bench width.
    """
    u = _unit(unit)
    width = TOPSET_WIDTH[u]["lower" if is_lower(lift) else "upper"]
    m = round_up(mid, STEP[u])
    return (round(m - width / 2, 4) + 0.0, round(m + width / 2, 4) + 0.0)


def backdown(top_mid, pct, step) -> float:
    """Back-down load = top-set midpoint x pct, CEILING to the step (CT-PLM-4 {M10}).

    pct is the block's fraction: 0.85-0.87 for 6-8-rep blocks, 0.88-0.89 for 3-5, 0.91-0.93 in PEAK.
    """
    p = float(pct)
    if not 0 < p < 1:
        raise ValueError(f"back-down pct is a fraction of the top-set midpoint, e.g. 0.88; got {pct!r}")
    return round_up(_mul(top_mid, p), step)


def _rir_text(lo: float, hi: float) -> str:
    """An RIR span as text: whole -> '2', a half -> the range around it ('1-2'); floors at 0 (F-8)."""
    a = max(0, math.floor(lo + TOL))
    b = max(0, math.ceil(hi - TOL))
    return str(a) if a == b else f"{a}-{b}"


def _rpe_bounds(rpe) -> tuple[float, float]:
    if isinstance(rpe, (tuple, list)):
        vals = [float(v) for v in rpe]
    elif isinstance(rpe, (int, float)) and not isinstance(rpe, bool):
        vals = [float(rpe)]
    else:
        s = str(rpe).strip()
        s = re.sub(r"(?i)^rpe\s*", "", s)
        s = s.replace("–", "-").replace("—", "-")
        s = re.sub(r"(?i)\s+to\s+", "-", s)
        try:
            vals = [float(p) for p in s.split("-")]
        except ValueError:
            raise ValueError(f"RPE {rpe!r} is not a number or a range like '8-8.5'") from None
    if not 1 <= len(vals) <= 2 or any(not 1 <= v <= 10 for v in vals):
        raise ValueError(f"RPE must be one or two values from 1 to 10, got {rpe!r}")
    return min(vals), max(vals)


def rpe_to_rir(rpe) -> str:
    """An RPE target written as RIR = 10 - RPE (CT-PLM-20 {M10}, A-5).

    Whole RPE gives one number (8 -> '2'); a half gives the range around it (7.5 -> '2-3',
    8.5 -> '1-2'). An RPE range maps end to end, so CT-PLM-20's "RPE 8 to 8.5" is '1-2'
    (8.5 alone is also '1-2'). Accepts 8, 8.5, '8-8.5', 'RPE 8 to 8.5' or (8, 8.5).
    """
    lo, hi = _rpe_bounds(rpe)
    return _rir_text(10 - hi, 10 - lo)


def topset_rpe(week, start=7.5, peak: bool = False) -> str:
    """The week's top-set RPE target inside a CT-PLM block (CT-PLM-5 {M10}).

    Follows the rule's own example, 7.5, 7.5 to 8, 8, 8 to 8.5: the target midpoint rises
    0.25 a week (the range's top end about 0.5), and a quarter value is written as the half-step
    range around it. It stays at RPE 9 or below outside PEAK. Pass the result to rpe_to_rir.
    """
    w = _whole(week, "week")
    if w < 1:
        raise ValueError(f"week must be 1 or more, got {week!r}")
    t = float(start) + 0.25 * (w - 1)
    if not peak:
        t = min(t, 9.0)
    lo = math.floor(t * 2 + TOL) / 2
    hi = math.ceil(t * 2 - TOL) / 2
    return _fmt(lo) if lo == hi else f"{_fmt(lo)}-{_fmt(hi)}"


def accessory_rir_plm(base_rir, week, deload: bool = False) -> str:
    """Accessory RIR in the topset-backdown template (CT-PLM-13 {M8}), as RIR text (CT-PLM-20).

    Against the week 1 base: weeks 2 and 3 at 0.5 below, week 4 at 1 below, never below 0;
    the deload at 1 above and at RIR 3 or more. A half value becomes a range (1.5 -> '1-2').
    """
    b = float(base_rir)
    if deload:
        x = max(b + 1, 3.0)
    else:
        offset = {1: 0.0, 2: 0.5, 3: 0.5, 4: 1.0}.get(_whole(week, "week"))
        if offset is None:
            raise ValueError(f"CT-PLM blocks have loading weeks 1-4, got {week!r}")
        x = max(b - offset, 0.0)
    return _rir_text(x, x)


# --- TM between cycles (L-9, L-10, L-11) ----------------------------------------------

def tm_increment(lift, unit) -> float:
    """The standard between-cycle TM rise (L-9 {M7}, F-11): +5 kg / +10 lb lower, +2.5 kg / +5 lb upper."""
    return INCREMENT[_unit(unit)]["lower" if is_lower(lift) else "upper"]


@dataclass
class _Amrap:
    weight: float
    reps: int
    minimum: int
    rpe: Optional[float] = None
    form_ok: Optional[bool] = None


def _minimum(v) -> int:
    m = re.fullmatch(r"\s*(\d+)\s*\+?\s*", str(v))
    if not m:
        raise ValueError(f"AMRAP minimum must be a number or '5+', got {v!r}")
    return int(m.group(1))


def _amrap(a) -> _Amrap:
    if isinstance(a, dict):
        mn = a.get("min_reps", a.get("minimum", a.get("min", a.get("target"))))
        return _Amrap(float(a["weight"]), int(a["reps"]), _minimum(mn),
                      None if a.get("rpe") is None else float(a["rpe"]), a.get("form_ok"))
    w, r, mn = a[0], a[1], a[2]
    return _Amrap(float(w), int(r), _minimum(mn))


def next_tm(tm, lift, amraps, unit, prior_e1rms=()) -> tuple[float, str]:
    """(new_tm, reason) for the next cycle of one lift.

    amraps: the cycle's AMRAP sets in the order done, each (weight, reps, minimum) or a dict
    {weight, reps, min_reps, rpe?, form_ok?}; minimum may be written '5+'.
    prior_e1rms: programming e1RMs (L-1) from earlier exposures, for the L-11 noise gate.

    In order:
      L-10  2 consecutive AMRAPs under their minimum: reset to 90% of the new e1RM (the most
            recent AMRAP of 1 to 10 reps) and tell the lifter. A reset never raises the TM.
      L-9   any miss: hold. Every AMRAP met: the standard increment.
      L-11  the TM moves beyond the standard increment only when the cycle's heaviest AMRAP
            (by load) has 10 reps or fewer, no grind past RPE 9.5, form not flagged, and an
            e1RM within 5% of a prior exposure; it then becomes 0.9 x that e1RM. A heaviest
            AMRAP over 10 reps is ignored for the TM (L-12), so the standard increment stands.
    L-10's other trigger, e1RM falling across 3 or more exposures without planned fatigue,
    needs the log's context and belongs to the check-in, not here.
    """
    u = _unit(unit)
    step = STEP[u]
    tm = float(tm)
    inc = tm_increment(lift, u)
    runs = [_amrap(a) for a in amraps]
    if not runs:
        return tm, f"hold: no AMRAP logged for {lift} this cycle; L-9 raises the TM only when every AMRAP met its minimum"

    missed = [a.reps < a.minimum for a in runs]
    if any(missed[i] and missed[i + 1] for i in range(len(missed) - 1)):
        latest = next((a for a in reversed(runs) if 1 <= a.reps <= 10), None)
        if latest is None:
            return tm, (f"L-10: {lift} missed 2 consecutive AMRAPs with no set of 1 to 10 reps to rebase on; "
                        "insert a deload or re-benchmark (W-1)")
        e = e1rm(latest.weight, latest.reps, step)
        reset = training_max(e, 0.90, step)
        if reset >= tm - TOL:
            return tm, (f"L-10: {lift} missed 2 consecutive AMRAPs but 90% of the new e1RM {_fmt(e)} "
                        f"is not below the TM; hold at {_fmt(tm)} {u} and tell the lifter")
        return reset, (f"reset (L-10): {lift} missed 2 consecutive AMRAPs; TM = 90% of the new e1RM "
                       f"{_fmt(e)} {u} ({_fmt(latest.weight)} x {latest.reps}), rounded up; tell the lifter")
    if any(missed):
        return tm, f"hold (L-9): {lift} missed an AMRAP minimum this cycle; TM stays {_fmt(tm)} {u}"

    std = round(tm + inc, 4)
    std_reason = f"+{_fmt(inc)} {u} (L-9): every {lift} AMRAP met its minimum"
    heaviest = max(runs, key=lambda a: a.weight)
    if heaviest.reps > 10:
        return std, std_reason + f"; the heaviest AMRAP ({heaviest.reps} reps) is over 10 and ignored for the TM (L-11, L-12)"
    if (heaviest.rpe is not None and heaviest.rpe > 9.5) or heaviest.form_ok is False:
        return std, std_reason + "; the heaviest AMRAP was a grind or broke form, so L-11 does not apply"
    e = e1rm(heaviest.weight, heaviest.reps, step)
    agree = [float(p) for p in prior_e1rms if p and abs(e - float(p)) <= 0.05 * float(p) + TOL]
    if agree:
        moved = training_max(e, 0.90, step)
        if moved > std + TOL:
            return moved, (f"L-11: heaviest AMRAP {_fmt(heaviest.weight)} x {heaviest.reps} gives e1RM {_fmt(e)} {u}, "
                           f"within 5% of a prior {_fmt(agree[0])}; TM = 90% of it, rounded up")
    return std, std_reason


# --- checks ------------------------------------------------------------------------------

class _Tally:
    """Collects one rule's results: a pass line, or the offending rows capped at CAP."""

    def __init__(self, rule: str):
        self.rule = rule
        self.n = 0
        self.bad: list[tuple[str, str, Optional[str]]] = []

    def ok(self):
        self.n += 1

    def add(self, status: str, detail: str, at: Optional[str] = None):
        self.n += 1
        self.bad.append((status, detail, at))

    def out(self, pass_detail: str, na_detail: str) -> list[Check]:
        if not self.bad:
            return [Check(self.rule, "pass" if self.n else "n/a", pass_detail if self.n else na_detail)]
        shown = [Check(self.rule, s, d, a) for s, d, a in self.bad[:CAP]]
        rest = self.bad[CAP:]
        if rest:
            status = "fail" if any(s == "fail" for s, _, _ in rest) else "warn"
            shown.append(Check(self.rule, status,
                               f"{len(rest)} more like this not listed ({len(self.bad)} in all)"))
        return shown


def _values(row) -> list:
    """Per-set load values: a list as written, or a scalar repeated for each set."""
    if row.load is None:
        return []
    if isinstance(row.load, list):
        return list(row.load)
    return [row.load] * max(int(row.sets or 1), 1)


def _reps_list(row) -> list[str]:
    s = str(row.reps or "").strip()
    if "," in s:
        return [p.strip() for p in s.split(",")]
    return [s] * max(int(row.sets or 1), 1)


_TM_BASIS = re.compile(r"\s*((?:\d+(?:\.\d+)?\s*%?\s*,\s*)*\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?TM\s*", re.I)


def _tm_pcts(basis) -> Optional[list[float]]:
    """'65% TM' -> [65.0]; '65%, 75% TM' -> [65.0, 75.0]; anything else -> None."""
    m = _TM_BASIS.fullmatch(str(basis or ""))
    if not m:
        return None
    return [float(p) for p in re.findall(r"\d+(?:\.\d+)?", m.group(1))]


def _family(name: str) -> str:
    n = str(name).lower()
    for key, fam in (("squat", "squat"), ("deadlift", "deadlift"), ("bench", "bench"),
                     ("overhead press", "ohp"), ("military press", "ohp"), ("ohp", "ohp")):
        if key in n:
            return fam
    return n


def _tm_for(program, exercise: str) -> Optional[float]:
    """The lift's TM: the exact exercise name, else the one TM key of the same family
    ('High Bar Squat' finds 'Squat'). Two candidates is ambiguous and finds nothing."""
    tms = program.tms or {}
    if exercise in tms:
        return _num(tms[exercise])
    fam = _family(exercise)
    hits = [k for k in tms if _family(k) == fam]
    return _num(tms[hits[0]]) if len(hits) == 1 else None


def _uses_olympic_bar(name: str) -> bool:
    """EZ-bar movements are 'barbell' in the library but don't use the 20 kg bar."""
    eq = library.equipment(name)
    return not ("ez_bar" in eq and "barbell" not in eq)


def _norm_warmup(s: str) -> str:
    s = re.sub(r"(?i)^\s*warm-?up\s*:?\s*", "", str(s or ""))
    return re.sub(r"\s+", " ", s.replace(" ,", ",")).strip().lower()


_WARMUP_LOAD = re.compile(r"(\d+(?:\.\d+)?)\s*x\s*\d+", re.I)
_KG = re.compile(r"\d\s*(?:kg|kgs|kilos?)\b", re.I)
_LB = re.compile(r"\d\s*(?:lb|lbs|pounds?)\b", re.I)


def checks(program: model.Program, profile: Optional[model.Profile] = None, **ctx) -> list[Check]:
    """L-4, L-5, L-6, F-5 and F-11 over a draft. One pass line per rule, or one line per
    offending row (at most 10 per rule, then a summary); n/a when there is nothing to check."""
    raw_unit = getattr(profile, "unit", None) or program.unit
    try:
        unit = _unit(raw_unit)
    except ValueError as e:
        na = "unit unknown; nothing checked"
        return [Check("F-11", "fail", str(e))] + [Check(r, "n/a", na) for r in ("L-4", "L-5", "L-6", "F-5")]
    micro = bool(getattr(profile, "microplates", False))
    step = step_for(unit, micro)
    std_step = STEP[unit]
    bar = BAR[unit]

    l4, l5, l6, f5, f11 = (_Tally(r) for r in ("L-4", "L-5", "L-6", "F-5", "F-11"))

    # L-4: TMs and e1RMs are computed numbers too.
    for label, table in (("TM", program.tms), ("e1RM", program.e1rms)):
        for lift, v in (table or {}).items():
            x = _num(v)
            at = where(exercise=f"{label} {lift}")
            if x is None:
                l4.add("fail", f"{label} {lift} is {v!r}, not a number", at)
            elif _is_multiple(x, step):
                l4.ok()
            else:
                l4.add("fail", f"{label} {lift} {_fmt(x)} is not a multiple of {_fmt(step)} {unit} (L-4: CEILING)", at)

    groups: dict[tuple[int, int, str], list] = {}   # (week, day, exercise) -> [(week obj, index, row)]
    missing_tm: dict[str, str] = {}

    for w in program.weeks:
        for d in w.days:
            for i, r in enumerate(d.rows, 1):
                at = where(w.week, d.day, r.exercise, i)
                vals = _values(r)

                # L-4: every computed load is a multiple of the step.
                if r.role in COMPUTED_ROLES:
                    for v in vals:
                        x = _num(v)
                        if x is None:
                            l4.add("fail", f"load {v!r} is not a number (L-4, IL-10)", at)
                        elif _is_multiple(x, step):
                            l4.ok()
                        else:
                            l4.add("fail", f"{_fmt(x)} {unit} is not a multiple of {_fmt(step)} {unit} (L-4: CEILING to the step)", at)

                # F-5: every barbell load is plate-loadable.
                if vals and library.is_barbell(r.exercise):
                    olympic = _uses_olympic_bar(r.exercise)
                    for v in vals:
                        x = _num(v)
                        if x is None:
                            f5.add("fail", f"barbell load {v!r} is not a number", at)
                        elif olympic and x < bar - TOL:
                            f5.add("fail", f"{_fmt(x)} {unit} work set is under the {_fmt(bar)} {unit} bar; "
                                           f"offer the lifter a dumbbell or technique-bar option", at)
                        elif not _is_multiple(x, step):
                            f5.add("fail", f"{_fmt(x)} {unit} is not plate-loadable (step {_fmt(step)} {unit})", at)
                        else:
                            f5.ok()

                # F-5 on the warm-up note: nothing under the bar, every load plate-loadable.
                if r.warmup:
                    for m in _WARMUP_LOAD.finditer(r.warmup):
                        x = float(m.group(1))
                        if x < bar - TOL:
                            f5.add("fail", f"warm-up load {_fmt(x)} {unit} is under the bar; write the bar ({_fmt(bar)})", at)
                        elif not _is_multiple(x, step):
                            f5.add("fail", f"warm-up load {_fmt(x)} {unit} is not plate-loadable (step {_fmt(step)} {unit})", at)
                        else:
                            f5.ok()

                # F-11: one unit throughout, no unit words that contradict it.
                wrong = _LB if unit == "kg" else _KG
                for field in ("basis", "warmup", "cue", "reason"):
                    text = getattr(r, field, None)
                    if text and wrong.search(str(text)):
                        f11.add("fail", f"{field} {text!r} names the other unit in a {unit} program", at)
                for v in vals:
                    if isinstance(v, str) and (_KG.search(v) or _LB.search(v)):
                        f11.add("fail", f"load {v!r} carries a unit; the file carries none (IL-19)", at)

                if r.role in WAVE_ROLES:
                    groups.setdefault((w.week, d.day, r.exercise), []).append((w, i, r))

                    # L-5: recompute each "% TM" row against the program's TM.
                    pcts = _tm_pcts(r.basis)
                    if pcts is None:
                        l5.add("warn", f"basis {r.basis!r} is not 'NN% TM'; load not verified", at)
                    else:
                        tm = _tm_for(program, r.exercise)
                        if tm is None:
                            missing_tm.setdefault(r.exercise, at)
                        elif len(pcts) not in (1, len(vals)):
                            l5.add("fail", f"basis lists {len(pcts)} percentages for {len(vals)} loads", at)
                        else:
                            each = pcts * len(vals) if len(pcts) == 1 else pcts
                            for pct, v in zip(each, vals):
                                x = _num(v)
                                exact = _mul(tm, pct / 100)
                                # L-4: with microplates the 1.25 step is allowed, not required.
                                ok = {round_up(exact, step), round_up(exact, std_step)}
                                if x is None:
                                    l5.add("fail", f"load {v!r} is not a number", at)
                                elif any(abs(x - e) <= TOL for e in ok):
                                    l5.ok()
                                else:
                                    l5.add("fail", f"load {_fmt(x)} but {_fmt(pct)}% of TM {_fmt(tm)} is "
                                                   f"{_fmt(round_up(exact, step))} {unit} (CEILING to {_fmt(step)})", at)

                    # L-5: only the last work set is the AMRAP, labelled 5+, 3+ or 1+.
                    reps = str(r.reps or "").strip()
                    if r.role == "main_amrap" and reps not in ("5+", "3+", "1+"):
                        l5.add("fail", f"AMRAP row reps {reps!r}; label it '5+', '3+' or '1+'", at)
                    elif r.role == "main" and "+" in reps:
                        l5.add("fail", f"main row reps {reps!r}; only the last work set is the AMRAP (role main_amrap)", at)

    for lift, at in missing_tm.items():
        l5.add("fail", f"no TM recorded for {lift}; benchmark it in week 1 (W-1) and issue later weeks "
                       f"from the result (W-5), never a guessed load", at)

    for (wk, dy, ex), members in groups.items():
        week_obj = members[0][0]
        first_i, first = members[0][1], members[0][2]
        at = where(wk, dy, ex)

        # F-5: a 5/3/1 wave's loads rise set by set; no repeats, no drops.
        seq = [_num(v) for _, _, r in members for v in _values(r)]
        seq = [x for x in seq if x is not None]
        if len(seq) > 1:
            if all(b > a + TOL for a, b in zip(seq, seq[1:])):
                f5.ok()
            else:
                f5.add("fail", f"5/3/1 wave does not rise: {', '.join(_fmt(x) for x in seq)} {unit}", at)

        # L-5: a group that ends in an AMRAP is one week of the wave, in the week's percentages.
        wave_week = (wk - 1) % 4 + 1
        if any(r.role == "main_amrap" for _, _, r in members) and not week_obj.deload and wave_week in WAVE:
            pcts, reps = [], []
            for _, _, r in members:
                p = _tm_pcts(r.basis)
                n = len(_values(r)) or max(int(r.sets or 1), 1)
                pcts += (p * n if p and len(p) == 1 else (p or [None] * n))
                reps += _reps_list(r)
            want_p = [round(p * 100, 4) for p, _ in WAVE[wave_week]]
            want_r = [x for _, x in WAVE[wave_week]]
            if None in pcts:
                pass  # rows without a % TM basis are already reported above
            elif len(pcts) != len(want_p) or any(abs(a - b) > TOL for a, b in zip(pcts, want_p)) or reps != want_r:
                l5.add("fail", f"week {wk} reads {'/'.join(_fmt(p) for p in pcts)}% x {'/'.join(reps)}; "
                               f"wave week {wave_week} is {'/'.join(_fmt(p) for p in want_p)}% x {'/'.join(want_r)}", at)
            else:
                l5.ok()

        # L-6: the first work row of each main lift carries the warm-up, matching L-6's numbers.
        at_first = where(wk, dy, ex, first_i)
        if not (first.warmup or "").strip():
            l6.add("fail", "first work row has no warm-up; L-6 is bar x20 then 40/50/60% TM x 5/5/3 (IL-17)", at_first)
        else:
            tm = _tm_for(program, ex)
            if tm is None:
                l6.ok()  # nothing to compare against; L-5 already reports the missing TM
            else:
                want = {warmup_note(tm, step, unit), warmup_note(tm, std_step, unit)}
                if _norm_warmup(first.warmup) in {_norm_warmup(x) for x in want}:
                    l6.ok()
                else:
                    l6.add("fail", f"warm-up reads {first.warmup!r}; L-6 gives {warmup_note(tm, step, unit)!r}", at_first)

    # F-11: the program's unit is the profile's.
    prog_unit = str(program.unit or "").strip().lower()
    if profile is not None and prog_unit != unit:
        f11.add("fail", f"program unit {program.unit!r} but the profile says {unit!r}; loads are in the profile unit (F-10)")
    else:
        f11.ok()

    lb_rules = "step 5 lb (2.5 with microplates), bar 45 lb, TM +10 lb lower / +5 lb upper"
    return (
        l4.out(f"{l4.n} computed loads are multiples of {_fmt(step)} {unit}", "no computed loads")
        + l5.out(f"{l5.n} main-set loads and waves match their % of TM", "no 5/3/1 main sets")
        + l6.out(f"{l6.n} main lifts carry the L-6 warm-up on their first work row", "no 5/3/1 main sets")
        + f5.out(f"{f5.n} barbell loads, warm-ups and waves are plate-loadable", "no barbell loads")
        + f11.out(f"{unit} throughout" + (f"; {lb_rules}" if unit == "lb" else ""), "nothing to check")
    )

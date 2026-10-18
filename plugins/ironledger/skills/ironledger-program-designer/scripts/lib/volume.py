"""Weekly fractional hard sets per muscle (rulebook P-2 to P-7 {M12}; ironledger-import LB-7).

Counting (P-2, LB-7): a hard set ends at 4 RIR or closer. Each hard set counts 1 for the
exercise's primary muscle (library muscleGroups[0]) and 0.5 for every other listed muscle.
`full_body`, a muscle outside IronLedger's taxonomy and an exercise the library doesn't know
are reported, never counted or guessed (G-11).

Bands (checks):
  P-2  always: the weekly table
  P-5  novice: 4 to 10 per muscle a week                                  -> warn
  P-3  intermediate/advanced hypertrophy (primary type HYP): priority muscles at least 10,
       every other directly trained muscle at least 6                      -> warn
  P-4  over 20 a week: warn, or departure when program.departures lists P-4
  P-7  over 11 in one session, or over 10 a week in fewer than 2 sessions  -> fail
Deload weeks are shown in the table but left out of the P-3/P-4/P-5 bands: L-7 and P-15 cut
their volume on purpose. P-7 applies to every week.
"""
from __future__ import annotations

import re
from typing import Optional

from lib import library, model
from lib.checks import Check, where

HARD_RIR = 4
CAP = 10
TOL = 1e-9

# IronLedger's muscle taxonomy (LB-7), in the table's display order. full_body is not a muscle.
MUSCLES = (
    "chest", "back", "lats", "traps", "shoulders", "biceps", "triceps", "forearms",
    "quadriceps", "hamstrings", "glutes", "calves", "abs", "obliques", "lower_back",
)
NOT_COUNTED = "full_body"
SYNONYMS = {"quads": "quadriceps", "hams": "hamstrings", "delts": "shoulders",
            "lower back": "lower_back", "abdominals": "abs", "core": "abs"}


# --- counting ----------------------------------------------------------------------------

_RIR_ENTRY = re.compile(r"(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?")


def _rir_lows(rir) -> Optional[list[float]]:
    """Lower bound of each RIR entry: '2' -> [2], '1-2' -> [1], '3-5' -> [3], '2, 2, 1' -> [2, 2, 1].
    None when the cell is blank or not an IL-12 form."""
    if rir is None or isinstance(rir, bool):
        return None
    if isinstance(rir, (int, float)):
        return [float(rir)]
    s = str(rir).strip()
    if not s:
        return None
    out = []
    for part in s.split(","):
        m = _RIR_ENTRY.fullmatch(part.strip())
        if not m:
            return None
        nums = [float(g) for g in m.groups() if g is not None]
        out.append(min(nums))
    return out


def is_hard(row: model.Row) -> bool:
    """True when the row's RIR lower bound is 4 or closer (P-2)."""
    lows = _rir_lows(row.rir)
    return lows is not None and min(lows) <= HARD_RIR


def _hard_set_count(row) -> int:
    """Hard sets in the row. A per-set RIR list is read set by set, and sets beyond the list
    take its last entry (EX-13), so '6, 4, 2' over 3 sets is 2 hard sets."""
    lows = _rir_lows(row.rir)
    sets = int(row.sets or 0)
    if lows is None or sets <= 0:
        return 0
    return sum(1 for i in range(sets) if lows[min(i, len(lows) - 1)] <= HARD_RIR)


def _breakdown(row) -> tuple[dict[str, float], list[str]]:
    """(counted {muscle: sets}, reasons something in the row went uncounted)."""
    n = _hard_set_count(row)
    if n == 0:
        return {}, []
    groups = library.muscles(row.exercise)
    if not groups:
        return {}, ["not in the library or alias table"]
    counted: dict[str, float] = {}
    skipped: list[str] = []
    for i, m in enumerate(groups):
        if m == NOT_COUNTED:
            skipped.append(NOT_COUNTED)
        elif m not in MUSCLES:
            skipped.append(f"unknown muscle {m}")
        else:
            counted[m] = counted.get(m, 0.0) + (1.0 if i == 0 else 0.5) * n
    return counted, skipped


def row_sets(row: model.Row) -> dict[str, float]:
    """{muscle: fractional sets} for one row: primary 1 per hard set, each other listed muscle 0.5 (P-2)."""
    return _breakdown(row)[0]


def _add(into: dict[str, float], more: dict[str, float]) -> None:
    for m, s in more.items():
        into[m] = into.get(m, 0.0) + s


def weekly_sets(program: model.Program) -> dict[int, dict[str, float]]:
    """{week: {muscle: fractional hard sets}}; every week appears, even an empty one (P-2)."""
    out: dict[int, dict[str, float]] = {}
    for w in program.weeks:
        tot = out.setdefault(w.week, {})
        for d in w.days:
            for r in d.rows:
                _add(tot, row_sets(r))
    return out


def session_sets(program: model.Program) -> dict[tuple[int, int], dict[str, float]]:
    """{(week, day): {muscle: fractional hard sets}} (P-7)."""
    out: dict[tuple[int, int], dict[str, float]] = {}
    for w in program.weeks:
        for d in w.days:
            tot = out.setdefault((w.week, d.day), {})
            for r in d.rows:
                _add(tot, row_sets(r))
    return out


def _uncounted(program) -> tuple[list[str], list[str]]:
    """(rows with something uncounted, rows whose RIR could not be read)."""
    skipped, unreadable = [], []
    for w in program.weeks:
        for d in w.days:
            for i, r in enumerate(d.rows, 1):
                if _rir_lows(r.rir) is None:
                    unreadable.append(f"{where(w.week, d.day, r.exercise, i)} (RIR {r.rir!r})")
                    continue
                _, why = _breakdown(r)
                if why:
                    skipped.append(f"{where(w.week, d.day, r.exercise, i)} ({'; '.join(why)})")
    return skipped, unreadable


def _fmt(x: float) -> str:
    return str(int(x)) if abs(x - round(x)) < TOL else f"{x:g}"


def _muscle_order(names) -> list[str]:
    known = [m for m in MUSCLES if m in names]
    return known + sorted(n for n in names if n not in MUSCLES)


def table(program: model.Program) -> str:
    """The P-2 weekly table: muscles as rows, weeks as columns, then what went uncounted."""
    weekly = weekly_sets(program)
    weeks = list(program.weeks)
    heads = [f"W{w.week}" + ("d" if w.deload else "") for w in weeks]
    seen = {m for tot in weekly.values() for m, s in tot.items() if s > 0}
    lines = ["Fractional hard sets per muscle per week (P-2)"]
    if not seen:
        lines.append("No hard sets counted.")
    else:
        name_w = max(len("Muscle"), *(len(m) for m in seen))
        col_w = max(4, *(len(h) for h in heads))
        lines.append("Muscle".ljust(name_w) + "".join(h.rjust(col_w + 2) for h in heads))
        for m in _muscle_order(seen):
            cells = [_fmt(weekly[w.week].get(m, 0.0)) for w in weeks]
            lines.append(m.ljust(name_w) + "".join(c.rjust(col_w + 2) for c in cells))
    lines.append("Primary muscle 1 per hard set, each other listed muscle 0.5; hard = RIR 4 or closer."
                 + (" d = deload week." if any(w.deload for w in weeks) else ""))
    skipped, unreadable = _uncounted(program)
    if skipped:
        lines.append("Not counted: " + "; ".join(skipped))
    if unreadable:
        lines.append("RIR unreadable, not counted: " + "; ".join(unreadable))
    return "\n".join(lines)


# --- checks ------------------------------------------------------------------------------

def _norm_muscle(m: str) -> str:
    s = str(m).strip().lower()
    return SYNONYMS.get(s, s.replace(" ", "_"))


def _priority(program, profile, ctx) -> list[str]:
    raw = (ctx.get("priority_muscles") or getattr(program, "priority_muscles", None)
           or getattr(profile, "priority_muscles", None) or [])
    return [_norm_muscle(m) for m in raw]


def _direct_muscles(program) -> set[str]:
    """Muscles that are some counted row's primary muscle anywhere in the program.

    P-3's "every other muscle" and P-5's per-muscle floor are read as the muscles the program
    trains directly: a muscle reached only as someone else's secondary (lower_back from a
    deadlift) is shown in the table but not held to a floor. Ceilings apply to every muscle.
    """
    out = set()
    for _, _, r in program.rows():
        if _hard_set_count(r) and library.muscles(r.exercise):
            m = library.muscles(r.exercise)[0]
            if m in MUSCLES:
                out.add(m)
    return out


def _departure(program, rule: str) -> Optional[dict]:
    for d in program.departures or []:
        if isinstance(d, dict) and str(d.get("rule", "")).strip().upper() == rule:
            return d
    return None


def _capped(rule: str, bad: list[tuple[str, str, Optional[str]]]) -> list[Check]:
    out = [Check(rule, s, d, a) for s, d, a in bad[:CAP]]
    rest = bad[CAP:]
    if rest:
        status = "fail" if any(s == "fail" for s, _, _ in rest) else "warn"
        out.append(Check(rule, status, f"{len(rest)} more like this not listed ({len(bad)} in all)"))
    return out


def checks(program: model.Program, profile: Optional[model.Profile] = None, **ctx) -> list[Check]:
    """P-2 (the table), P-3/P-4/P-5 (warn bands by training status and goal), P-7 (fail).

    ctx may carry priority_muscles=[...] (CT-HYP-4); the program or profile may also carry it.
    """
    weekly = weekly_sets(program)
    sessions = session_sets(program)
    loading = [w for w in program.weeks if not w.deload]
    status = str(getattr(profile, "training_status", None) or "").strip().lower()
    goal = str(program.primary_type or getattr(profile, "primary_type", None) or "").strip().upper()
    goal = goal[3:] if goal.startswith("CT-") else goal
    direct = _direct_muscles(program)
    out: list[Check] = []

    # P-2: always report the table. Unreadable RIR means the count may be short.
    _, unreadable = _uncounted(program)
    out.append(Check("P-2", "warn" if unreadable else "pass", table(program)))

    # P-5: novices 4 to 10 per muscle a week.
    if not status:
        out.append(Check("P-5", "warn", "training status not set (P-1); the novice 4-10 band was not checked"))
    elif status != "novice":
        out.append(Check("P-5", "n/a", f"{status} lifter; the novice band does not apply"))
    else:
        bad = []
        for w in loading:
            tot = weekly.get(w.week, {})
            notes = [f"{m} {_fmt(tot.get(m, 0.0))} (below 4)" for m in _muscle_order(direct) if tot.get(m, 0.0) < 4 - TOL]
            notes += [f"{m} {_fmt(s)} (above 10)" for m, s in sorted(tot.items()) if s > 10 + TOL]
            if notes:
                bad.append(("warn", "novice band 4-10 a week: " + ", ".join(notes), where(w.week)))
        out += _capped("P-5", bad) if bad else [Check("P-5", "pass" if loading else "n/a",
                                                      "every directly trained muscle is within 4-10 a week"
                                                      if loading else "no loading weeks")]

    # P-3: intermediate/advanced hypertrophy. The 20 ceiling is enforced once, under P-4.
    if goal != "HYP":
        out.append(Check("P-3", "n/a", (f"goal {goal} is" if goal else "no primary type set, so the goal is")
                         + " not hypertrophy; volumes are reported in P-2 only"))
    elif not status:
        out.append(Check("P-3", "warn", "training status not set (P-1); the hypertrophy band was not checked"))
    elif status == "novice":
        out.append(Check("P-3", "n/a", "novice lifter; P-5's band applies"))
    else:
        prio = _priority(program, profile, ctx)
        bad = []
        for w in loading:
            tot = weekly.get(w.week, {})
            notes = [f"priority {m} {_fmt(tot.get(m, 0.0))} (below 10)" for m in prio if tot.get(m, 0.0) < 10 - TOL]
            notes += [f"{m} {_fmt(tot.get(m, 0.0))} (below 6)" for m in _muscle_order(direct)
                      if m not in prio and tot.get(m, 0.0) < 6 - TOL]
            if notes:
                bad.append(("warn", "hypertrophy band: " + ", ".join(notes), where(w.week)))
        if not prio:
            bad.append(("warn", "no priority muscles named (CT-HYP-4); every trained muscle was held to at least 6", None))
        out += _capped("P-3", bad) if bad else [Check("P-3", "pass" if loading else "n/a",
                                                      f"priority {', '.join(prio)} at 10+ and every other trained muscle at 6+"
                                                      if loading else "no loading weeks")]

    # P-4: over 20 a week only with a recorded, tolerated specialisation (a departure).
    over = [(w.week, m, s) for w in loading for m, s in sorted(weekly.get(w.week, {}).items()) if s > 20 + TOL]
    if not over:
        out.append(Check("P-4", "pass" if loading else "n/a",
                         "no muscle over 20 fractional sets a week" if loading else "no loading weeks"))
    else:
        dep = _departure(program, "P-4")
        muscles = sorted({m for _, m, _ in over})
        text = ", ".join(f"W{wk} {m} {_fmt(s)}" for wk, m, s in over)
        if dep:
            extra = "; more than 2 specialisation muscles" if len(muscles) > 2 else ""
            out.append(Check("P-4", "departure", f"over 20 a week: {text}{extra}; departure: {dep.get('reason', '')}"))
        else:
            out.append(Check("P-4", "warn", f"over 20 a week: {text}; needs logged tolerance and a recorded departure, "
                                            "for at most 2 specialisation muscles"))

    # P-7: at most 11 in one session; over 10 a week needs 2 or more sessions.
    bad = []
    for (wk, dy), tot in sessions.items():
        for m, s in sorted(tot.items()):
            if s > 11 + TOL:
                bad.append(("fail", f"{m} gets {_fmt(s)} fractional sets in one session (over 11)", where(wk, dy)))
    for wk, tot in weekly.items():
        for m, s in sorted(tot.items()):
            if s > 10 + TOL:
                days = [dy for (w2, dy), t in sessions.items() if w2 == wk and t.get(m, 0.0) > 0]
                if len(days) < 2:
                    bad.append(("fail", f"{m} gets {_fmt(s)} sets this week in {len(days)} session; "
                                        "over 10 needs at least 2 sessions", where(wk)))
    if bad:
        out += _capped("P-7", bad)
    else:
        any_sets = any(s > 0 for tot in weekly.values() for s in tot.values())
        out.append(Check("P-7", "pass" if any_sets else "n/a",
                         "no muscle over 11 in a session; every muscle over 10 a week is split over 2+ sessions"
                         if any_sets else "no hard sets counted"))
    return out

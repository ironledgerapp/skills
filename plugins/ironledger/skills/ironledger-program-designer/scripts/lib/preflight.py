"""Pre-flight: every rule check in one report (rulebook.md G-7).

A draft goes to the lifter only when this report has no `fail`. A failing rule that
the program lists in `program.departures` with a reason becomes `departure`:
still shown, never hidden, and not blocking (G-7).

Module checks come from loads, volume and ironledger_io; the checks here are
the ones no single module owns: the screen and age gates, names, dislikes,
effort floors, days, and the unconfirmed decisions a draft relied on.
"""
from __future__ import annotations

import importlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field

from lib import library, model
from lib.checks import Check, where

MODULES = ("loads", "volume", "ironledger_io")

# Gates and the lifter's own constraints can never be turned into a departure
# (G-7 covers rules that may reasonably give; these may not). A departure naming
# one is ignored and itself reported as a fail.
NON_DEPARTABLE = {"G-4", "G-7", "G-16", "CT-JUN-1", "A-8"}


def rir_low(text: str):
    """Lower bound of an RIR cell ("2", "1-2", "3-5", "2, 2, 1"), or None if unreadable."""
    nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text or "")]
    return min(nums) if nums else None


def _strings(program: model.Program):
    """Every free-text field in the program, with where it came from."""
    for w, d, r in program.rows():
        for f in ("basis", "cue", "reason", "warmup", "tempo", "rest", "superset"):
            v = getattr(r, f)
            if v:
                yield where(w.week, d.day, r.exercise), v
    for w in program.weeks:
        for d in w.days:
            if d.label:
                yield where(w.week, d.day), d.label
            for x in d.extras:
                yield where(w.week, d.day), x
    for dep in program.departures:
        yield "departures", dep.get("reason", "")


def own_checks(program: model.Program, profile: model.Profile) -> list[Check]:
    out: list[Check] = []

    # G-4 screen gate (APSS Stage 1); CT-JUN-1 no program for anyone under 18.
    out.append(Check("G-4", "pass" if profile.screen_cleared else "fail",
                     "screen passed: no to all six APSS Stage 1 questions, or a health professional's go-ahead"
                     if profile.screen_cleared else
                     "screen not passed: the lifter must answer no to all six APSS Stage 1 questions, "
                     "or have guidance from a health professional, before any program"))
    if str(profile.age_band or "").lower() == "junior":
        out.append(Check("CT-JUN-1", "fail", "the lifter is under 18; this skill writes no program for them. "
                                             "Heavy lifting for under-18s needs a qualified coach's supervision (CT-JUN-3)"))

    # F-7 / A-9: every exercise is a library name or an approved alias.
    unknown = Counter(r.exercise for _, _, r in program.rows() if not library.known(r.exercise))
    out.append(Check("F-7", "fail", "not in the library or approved aliases: " + ", ".join(sorted(unknown)))
               if unknown else Check("F-7", "pass", "every exercise name is a library name or approved alias"))

    # A-8 / G-15: nothing disliked or ruled out.
    banned = {n.lower() for n in profile.dislikes + profile.avoid}
    hits = [(w, d, r) for w, d, r in program.rows() if r.exercise.lower() in banned]
    for w, d, r in hits[:10]:
        out.append(Check("A-8", "fail", f"{r.exercise} is on the lifter's dislike or avoid list", where(w.week, d.day, r.exercise)))
    if not hits:
        out.append(Check("A-8", "pass", "no disliked or ruled-out exercise"))

    # P-9 every row has an effort cap; A-5 effort is RIR, never RPE, in import files.
    no_rir = [(w, d, r) for w, d, r in program.rows() if not (r.rir or "").strip()]
    for w, d, r in no_rir[:10]:
        out.append(Check("P-9", "fail", "row has no RIR cap", where(w.week, d.day, r.exercise)))
    if not no_rir:
        out.append(Check("P-9", "pass", "every row has an RIR target or cap"))
    rpe = [(w, d, r) for w, d, r in program.rows() if "rpe" in (r.rir or "").lower()]
    out.append(Check("A-5", "fail", f"RPE written in an RIR cell ({len(rpe)} rows)", where(rpe[0][0].week, rpe[0][1].day, rpe[0][2].exercise))
               if rpe else Check("A-5", "pass", "effort is written as RIR"))

    # A-7 no planned failure on free-weight compounds.
    zero = [(w, d, r) for w, d, r in program.rows()
            if library.is_free_weight(r.exercise) and library.is_compound(r.exercise) and rir_low(r.rir) == 0]
    for w, d, r in zero[:10]:
        out.append(Check("A-7", "fail", f"RIR 0 planned on a free-weight compound ({r.exercise})", where(w.week, d.day, r.exercise)))
    if not zero:
        out.append(Check("A-7", "pass", "no planned failure on free-weight compounds"))

    # CT-SEL-7 training days never exceed what the lifter has.
    most = max((len(w.days) for w in program.weeks), default=0)
    if profile.days is None:
        out.append(Check("CT-SEL-7", "warn", "profile has no available-days figure"))
    else:
        out.append(Check("CT-SEL-7", "fail" if most > profile.days else "pass",
                         f"{most} training days in the busiest week; the lifter has {profile.days}"))

    # P-13 each row names its progression model; P-1 training status known.
    unnamed = sum(1 for _, _, r in program.rows() if not r.progression)
    out.append(Check("P-13", "warn" if unnamed else "pass",
                     f"{unnamed} rows don't name a progression model" if unnamed else "every row names its progression model"))
    out.append(Check("P-1", "pass" if profile.training_status else "warn",
                     f"training status: {profile.training_status}" if profile.training_status else "profile has no training status"))

    # F-9 the method decisions this draft relied on (always shown to the lifter).
    relied = ", ".join(program.decisions_relied_on) or "none"
    out.append(Check("F-9", "pass", f"method decisions relied on: {relied}"))
    return out


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return any(c.status == "fail" for c in self.checks)

    def counts(self) -> dict[str, int]:
        return dict(Counter(c.status for c in self.checks))

    def to_dict(self) -> dict:
        return {"failed": self.failed, "counts": self.counts(),
                "checks": [c.__dict__ for c in self.checks]}

    def render(self) -> str:
        order = {"fail": 0, "departure": 1, "warn": 2, "pass": 3, "n/a": 4}
        lines = [f"PRE-FLIGHT {'FAILED' if self.failed else 'PASSED'}  " +
                 "  ".join(f"{k}:{v}" for k, v in sorted(self.counts().items(), key=lambda kv: order[kv[0]]))]
        for c in sorted(self.checks, key=lambda c: (order[c.status], c.rule)):
            loc = f"  [{c.where}]" if c.where else ""
            lines.append(f"  {c.status.upper():9} {c.rule:10} {c.detail}{loc}")
        return "\n".join(lines)


def _apply_departures(program: model.Program, checks: list[Check]) -> None:
    reasons = {d["rule"]: d.get("reason", "") for d in program.departures if d.get("rule")}
    for rule in sorted(set(reasons) & NON_DEPARTABLE):
        checks.append(Check("G-7", "fail", f"{rule} is a gate or the lifter's own constraint and can't be departed from"))
        reasons.pop(rule)
    for c in checks:
        if c.status == "fail" and c.rule in reasons and reasons[c.rule].strip():
            c.status = "departure"
            c.detail = f"{c.detail} (departure: {reasons[c.rule]})"
    for rule, reason in reasons.items():
        if not reason.strip():
            checks.append(Check("G-7", "fail", f"departure from {rule} has no written reason"))


def run(program: model.Program, profile: model.Profile, csv_path: str | None = None) -> Report:
    checks = own_checks(program, profile)
    if profile.client != program.client:
        checks.append(Check("G-16", "fail", f"profile is {profile.client}, program is {program.client}"))
    for name in MODULES:
        mod = importlib.import_module(f"lib.{name}")
        kwargs = {"csv_path": csv_path} if name == "ironledger_io" else {}
        checks.extend(mod.checks(program, profile, **kwargs))
    _apply_departures(program, checks)
    return Report(checks)


def main_json(report: Report) -> str:
    return json.dumps(report.to_dict(), indent=2)

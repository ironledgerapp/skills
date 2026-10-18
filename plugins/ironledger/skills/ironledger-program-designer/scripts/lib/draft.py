"""The draft generator: template + lifter profile + benchmark sets (+ slot choices) -> a designer-program/1 Program.

The skill chooses the template and the accessory slots; every number comes from here and
lib.loads (rulebook G-6). The templates are data in assets/templates/*.json, documented in
assets/templates/README.md.

  generate(template_id, profile, benchmarks, *, block=1, choices=None, days=None, phase=None)
      -> (Program, notes)
  generate_one_off(template_id, profile, benchmarks, *, block=1, choices=None, days=None)
      -> (block N Program, block N+1 Program, notes)      a one-off program's two blocks (OO-1)

  benchmarks  {lift: {"weight", "reps", "rir"?, "age_weeks"?, "logged"?}}; a lift that has no set
              yet may carry {"estimate": e1RM} instead, which feeds its W-1 benchmark ramp (W-5)
  choices     {slot_id: "Exercise"} or {slot_id: {"exercise": ..., "reason": ...}} (A-8, G-15)
  days        the layout to use (CT-SEL-7); None takes the template default, or the lifter's days
              when they have fewer
  phase       topset-backdown only: "prep2" (default) or "peak" (CT-PLM-6)

Rules implemented here (the rest live in the templates and in lib.loads):
  L-1 to L-3   e1RM from the benchmark set, TM 90%, or 85% for novice or returning lifters and
               uncertain benchmarks (older than 8 weeks, self-reported, or rated RIR 3 or more)
  W-1, W-5     a main lift with no benchmark gets a week-1 benchmark session and is left out of
               later weeks until the block is re-issued (IL-20)
  CT-SEL-7     never more days than the lifter has; a missing layout is refused, never squeezed
  CT-SEL-8     equipment; CT-NOV-1 weeks 1-2 at RIR 3 or more; CT-NOV-2 novices on 5/3/1
  CT-HYP-3/A-7 no planned RIR 0 on a free-weight compound
  A-3, IL-30   AMRAP Last Set rows; CT-PLM-3/4/5/6/13/20 top sets and back-downs
  CT-JUN-1     no program for anyone under 18
  OO-1 to OO-6 two blocks at once: both 4-week blocks, every main lift benchmarked, block N+1's TMs
               at block N's plus the L-9 increment, and the lifter's own L-9 check recorded
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Optional

from lib import library, loads, model

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "templates"
TEMPLATE_SCHEMA = "designer-template/1"
ENGINES = ("531", "topset", "rotation", "fixed")
ALWAYS_AVAILABLE = frozenset({"bodyweight", "none"})   # needs no kit the profile has to list
NOTE_WORD_CAP = 20                                     # VO-1, applied by IL-14
PERCENT_RIR = "3-5"                                    # IL-30 default cap on percentage rows
LAST_SET_RIR = "0-1"                                   # IL-30, A-3
LAST_SET_CUE = "stop with 0 to 1 good reps left"
NOV_FLOOR = 3                                          # CT-NOV-1
NOV_CUE = "stop with about 3 good reps left"           # CT-NOV-3: a margin, never to failure
RAMP_RIR = "5-10"                                      # a W-1 ramp is not a hard set (P-2)
UNCERTAIN_AGE_WEEKS = 8                                # L-2, L-3
# OO-2: 4-week blocks whose loads never wait for a re-issue. The rest, and why each is refused.
ONE_OFF_TEMPLATES = ("531-4day", "531-2x", "531-club", "adf-prep", "pt-general")
ONE_OFF_REFUSED = {
    "topset-backdown": "a meet prep is planned one block at a time, with attempts chosen near the meet",
    "hypertrophy-rotation": "its blocks are 6 weeks, not 4",
}


class DraftError(ValueError):
    """The draft can't be generated as asked. The message names the rule and what to do."""


# --- templates -------------------------------------------------------------------------------

def template_ids() -> list[str]:
    return sorted(p.stem for p in TEMPLATE_DIR.glob("*.json"))


def load_template(template_id: str) -> dict:
    path = TEMPLATE_DIR / f"{template_id}.json"
    if not path.is_file():
        raise DraftError(f"no template {template_id!r}; the templates are {', '.join(template_ids())}")
    t = json.loads(path.read_text(encoding="utf-8"))
    if t.get("schema") != TEMPLATE_SCHEMA or t.get("id") != template_id:
        raise DraftError(f"{path.name} is not a {TEMPLATE_SCHEMA} template for {template_id!r}")
    return t


def _layout_slots(layout: dict) -> list[dict]:
    return [s for d in layout.get("days", []) for s in d.get("slots", [])]


def validate_template(t: dict) -> list[str]:
    """Problems with a template file: unknown names, layouts whose day count doesn't match
    their key, duplicate slot ids, missing fields. An empty list means it is usable."""
    out: list[str] = []
    for key in ("id", "engine", "client_types", "default_days", "decisions_relied_on",
                "equipment_required", "layouts"):
        if key not in t:
            out.append(f"missing {key!r}")
    if t.get("engine") not in ENGINES:
        out.append(f"engine {t.get('engine')!r} is not one of {ENGINES}")
    if t.get("engine") == "topset":
        if not t.get("phases"):
            out.append("topset template has no phases")
    elif not t.get("weeks"):
        out.append("no weeks")
    if str(t.get("default_days")) not in t.get("layouts", {}):
        out.append(f"default_days {t.get('default_days')} has no layout")
    for key, layout in t.get("layouts", {}).items():
        if len(layout.get("days", [])) != int(key):
            out.append(f"layout {key} has {len(layout.get('days', []))} days")
        seen = set()
        for d in layout.get("days", []):
            for lift in d.get("main", []) + d.get("topsets", []) + [s.get("lift") for s in d.get("second", [])]:
                if not library.known(lift):
                    out.append(f"layout {key}: main lift {lift!r} is not a library name")
            for s in d.get("slots", []):
                if s.get("id") in seen:
                    out.append(f"layout {key}: duplicate slot id {s.get('id')!r}")
                seen.add(s.get("id"))
                for name in [s.get("exercise")] + list(s.get("alternatives", [])) + \
                        [o.get("exercise") for o in s.get("by_type", {}).values() if o.get("exercise")] + \
                        [a for o in s.get("by_type", {}).values() for a in o.get("alternatives", [])]:
                    if not library.known(name):
                        out.append(f"layout {key} slot {s.get('id')}: {name!r} is not a library name (LB-1)")
                for need in ("id", "exercise", "sets"):
                    if need not in s:
                        out.append(f"layout {key}: a slot has no {need!r}")
    variant = t.get("variant")
    if variant and not library.known(variant.get("exercise")):
        out.append(f"variant {variant.get('exercise')!r} is not a library name")
    return out


# --- small helpers ---------------------------------------------------------------------------

def _fmt(x) -> str:
    s = f"{float(x):.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _pct(p) -> str:
    return _fmt(Decimal(repr(float(p))) * 100)


def _lower(items) -> set[str]:
    return {str(x).strip().lower() for x in (items or [])}


def _rir_bounds(rir: str) -> tuple[int, int, bool]:
    m = re.fullmatch(r"\s*(\d+)\s*(?:-\s*(\d+))?\s*", str(rir))
    if not m:
        raise DraftError(f"RIR {rir!r} is not '2' or '1-2' (IL-12)")
    lo = int(m.group(1))
    return lo, int(m.group(2)) if m.group(2) else lo, m.group(2) is not None


def _rir_text(lo: int, hi: int, was_range: bool) -> str:
    if was_range and hi == lo:
        hi = lo + 1   # a range stays a range, so the logger never auto-writes it (IL-30)
    return str(lo) if hi == lo else f"{lo}-{hi}"


def _floor_rir(rir: str, floor: int) -> str:
    """Raise an RIR target to at least `floor` (CT-NOV-1): '2' -> '3', '1-2' -> '3-4', '3-5' stays."""
    lo, hi, rng = _rir_bounds(rir)
    lo2 = max(lo, floor)
    return _rir_text(lo2, max(hi, lo2), rng)


def _fw_compound(name: str) -> bool:
    return library.is_free_weight(name) and library.is_compound(name)


def _is_bodyweight(name: str) -> bool:
    e = library.entry(name) or {}
    return e.get("category") == "bodyweight"


def _top_of_range(reps: str) -> str:
    return str(reps).split("-")[-1].strip()


# --- the context of one draft --------------------------------------------------------------

@dataclass
class _Ctx:
    t: dict
    profile: model.Profile
    block: int
    unit: str
    step: float
    ptype: str
    engine: str
    notes: list = field(default_factory=list)
    tms: dict = field(default_factory=dict)
    e1rms: dict = field(default_factory=dict)
    pending: dict = field(default_factory=dict)   # lift -> W-1 ramp estimate (W-5)
    picks: dict = field(default_factory=dict)     # slot id -> (exercise, reason)
    tm85: list = field(default_factory=list)      # the lifter-level reasons for TM 85% (L-3)
    nov_floor: bool = False                        # CT-NOV-1: weeks 1-2 at RIR 3 or more
    avail: Optional[set] = None                    # usable equipment, None when unknown
    a7_bumped: set = field(default_factory=set)

    def note(self, text: str) -> None:
        if text not in self.notes:
            self.notes.append(text)


# --- gates ---------------------------------------------------------------------------------

def _gate(t: dict, profile: model.Profile) -> None:
    """G-4 and CT-JUN-1: refuse before anything is drafted."""
    problems = []
    if not profile.screen_cleared:
        problems.append("G-4: the lifter hasn't passed the screen: answer no to all six APSS Stage 1 questions, "
                        "or get guidance from a health professional first, then set screen_cleared")
    if str(profile.age_band or "").lower() == "junior":
        problems.append("CT-JUN-1: the lifter is under 18. This skill writes no program for them; heavy lifting "
                        "for under-18s needs a qualified coach's supervision (CT-JUN-3)")
    if problems:
        raise DraftError("; ".join(problems))


def _primary_type(t: dict, profile: model.Profile, ctx_notes: list) -> str:
    ptype = str(profile.primary_type or "").strip().upper()
    ptype = ptype[3:] if ptype.startswith("CT-") else ptype
    types = t["client_types"]
    if not ptype:
        ctx_notes.append(f"CT-SEL-1: the profile has no primary type; the draft records {types[0]}, "
                         "the template's first type. Confirm it.")
        return types[0]
    if ptype in types:
        return ptype
    lacking = [e for e in t.get("any_type_without", []) if e not in set(profile.equipment)]
    if lacking and profile.equipment:
        ctx_notes.append(f"CT-SEL-8: primary type {ptype} drafted on {t['id']} because the lifter has no "
                         f"{', '.join(lacking)}.")
        return ptype
    if ptype == "RGI" and t["id"] == "531-club":
        raise DraftError("CT-RGI-10: in-season rugby rules (1 to 3 sets of 3 to 5 at 80 to 85% of e1RM, no wave, "
                         "no AMRAP) are not in 531-club yet; this skill can't draft an in-season block")
    raise DraftError(f"CT-SEL-1: template {t['id']} is for {', '.join(types)}; this lifter's primary type is "
                     f"{ptype}. Use that type's template from the client-types selection table")


def _pick_layout(t: dict, profile: model.Profile, days, notes: list) -> tuple[dict, int]:
    """CT-SEL-7: the layout for the days asked for, never more than the lifter has."""
    layouts = t["layouts"]
    have = profile.days
    if days is None:
        n = int(t["default_days"])
        if have is not None and have < n:
            n = int(have)
    else:
        n = int(days)
    if have is None:
        notes.append(f"CT-SEL-7: the profile has no available-days figure; drafted {n} days. Confirm it.")
    elif n > have:
        raise DraftError(f"CT-SEL-7: {n} training days asked for, but the lifter has {have}. Never more days "
                         "than the lifter has")
    if n < 2 and str(n) not in layouts:
        raise DraftError(f"CT-SEL-7: {n} training day a week has no template; CT-GEN-3's time-minimum plan has no template yet")
    if str(n) not in layouts:
        raise DraftError(f"CT-SEL-7: template {t['id']} has no {n}-day layout (it has "
                         f"{', '.join(sorted(layouts, key=int))}). Pick another template from the client-types selection table. "
                         "Never squeeze a longer layout into fewer days")
    if n != int(t["default_days"]):
        notes.append(f"CT-SEL-7: {n}-day layout ({layouts[str(n)].get('source', 'reduced-day layout')}).")
    return layouts[str(n)], n


# --- slots: defaults, alternatives and the skill's choices -------------------------------------------

def _unusable(name: str, ctx: _Ctx) -> Optional[str]:
    """Why an exercise can't go in this lifter's draft, or None when it can."""
    if not library.known(name):
        return "it is not in the library or the approved aliases (F-7, A-9)"
    if name.strip().lower() in _lower(ctx.profile.dislikes):
        return "it is on the lifter's dislike list (A-8)"
    if name.strip().lower() in _lower(ctx.profile.avoid):
        return "it is on the lifter's avoid list (G-15)"
    if ctx.avail is not None:
        missing = [e for e in library.equipment(name) if e not in ctx.avail]
        if missing:
            kit = {str(e) for e in ctx.profile.equipment}
            if ctx.t.get("equipment_ceiling") and not (kit and any(e not in kit for e in missing)):
                where = "this template's basic club gym leaves out (CT-RGO-15)"
            else:
                where = "the profile doesn't list (G-15)"
            return f"it needs {', '.join(missing)}, which {where}"
    return None


def _auto_reason(default: str, ctx: _Ctx) -> Optional[str]:
    """VO-4 and A-8: the Notes reason when a default gives way to a dislike or an avoid-list entry."""
    low = default.strip().lower()
    if low in _lower(ctx.profile.dislikes):
        return f"Replaces {default}, which you said you dislike"
    if low in _lower(ctx.profile.avoid):
        return f"Replaces {default}, which is off your list for now"
    return None


def _slot_spec(slot: dict, ptype: str) -> dict:
    spec = dict(slot)
    over = slot.get("by_type", {}).get(ptype)
    if over:
        spec.update(over)
    return spec


def _check_choices(choices, layout: dict, ctx: _Ctx) -> None:
    slots = {s["id"]: _slot_spec(s, ctx.ptype) for s in _layout_slots(layout)}
    for sid, value in (choices or {}).items():
        if sid not in slots:
            raise DraftError(f"choice for slot {sid!r}, which this layout doesn't have; its slots are "
                             f"{', '.join(slots)}")
        if isinstance(value, str):
            name, reason = value, None
        elif isinstance(value, dict) and isinstance(value.get("exercise"), str):
            name, reason = value["exercise"], value.get("reason")
        else:
            raise DraftError(f"choice for {sid} must be an exercise name or {{'exercise': ..., 'reason': ...}}")
        why = _unusable(name, ctx)
        if why:
            raise DraftError(f"choice for {sid}: {name!r} can't be used: {why}")
        default = slots[sid]["exercise"]
        if not (reason or "").strip():
            reason = _auto_reason(default, ctx) if name != default else None
        ctx.picks[sid] = (name, (reason or "").strip() or None)


def _resolve(slot: dict, ctx: _Ctx) -> tuple[str, Optional[str]]:
    """The slot's exercise and any A-8 reason: the skill's choice, else the default or the first usable alternative."""
    if slot["id"] in ctx.picks:
        return ctx.picks[slot["id"]]
    default = slot["exercise"]
    skipped = []
    for name in [default] + list(slot.get("alternatives", [])):
        why = _unusable(name, ctx)
        if why is None:
            if name != default:
                ctx.note(f"{slot['id']}: {default} can't be used, as {skipped[0][1]}; using {name}.")
            return name, _auto_reason(default, ctx) if name != default else None
        skipped.append((name, why))
    raise DraftError(f"slot {slot['id']}: no usable exercise ("
                     + "; ".join(f"{n}: {w}" for n, w in skipped)
                     + "). Pass one in choices, from the substitution table (subs)")


# --- benchmarks, e1RM and TM (L-1 to L-3, W-1, W-5) ----------------------------------------------

def _required_lifts(t: dict, layout: dict) -> list[str]:
    lifts: list[str] = []
    for d in layout["days"]:
        lifts += d.get("main", []) + [s["lift"] for s in d.get("second", [])] + d.get("topsets", [])
    if t["engine"] == "topset" and any(d.get("variant") for d in layout["days"]) and t.get("variant"):
        lifts.append(t["variant"]["of"])
    return list(dict.fromkeys(lifts))


def _uncertain(b: dict, ctx: _Ctx, lift: str) -> list[str]:
    """L-3's uncertain benchmark: older than 8 weeks, self-reported rather than logged, or rated RIR 3 or more."""
    why = []
    try:
        age = None if b.get("age_weeks") is None else float(b["age_weeks"])
        rir = None if b.get("rir") is None else float(b["rir"])
    except (TypeError, ValueError):
        raise DraftError(f"{lift} benchmark: age_weeks {b.get('age_weeks')!r} and rir {b.get('rir')!r} must be "
                         "numbers (L-3)") from None
    if age is not None and age > UNCERTAIN_AGE_WEEKS:
        why.append(f"benchmark {_fmt(age)} weeks old (over {UNCERTAIN_AGE_WEEKS})")
    if b.get("logged") is False:
        why.append("benchmark self-reported, not logged")
    elif b.get("logged") is None:
        ctx.note(f"{lift}: the benchmark doesn't say whether it was logged; treated as logged (L-3). Confirm it.")
    if rir is not None and rir >= 3:
        why.append(f"benchmark rated RIR {_fmt(rir)}")
    return why


def _measured(b) -> bool:
    """CT-NOV-2: a measured benchmark set of 2 to 8 reps (not an estimate)."""
    try:
        return bool(b) and b.get("weight") is not None and 2 <= float(b.get("reps")) <= 8
    except (TypeError, ValueError):
        return False


def _benchmarks(lifts: list[str], benchmarks: dict, ctx: _Ctx) -> None:
    """e1RM (L-1, L-2) and TM (L-3) for each lift, with notes; lifts with only an estimate wait for W-5."""
    cfg = ctx.t.get("benchmark", {})
    unit, missing = ctx.unit, []
    for lift in lifts:
        b = (benchmarks or {}).get(lift) or {}
        if b.get("weight") is not None and b.get("reps") is not None:
            try:
                w, r = float(b["weight"]), b["reps"]
                if isinstance(r, bool) or not float(r).is_integer():
                    raise ValueError(f"reps must be a whole number, got {r!r}")
                r = int(r)
                if r > 10:
                    raise ValueError(f"{r} reps; L-2 takes a set of 10 reps at most (6 or fewer preferred)")
                e = loads.e1rm(w, r, ctx.step)
            except ValueError as err:
                raise DraftError(f"{lift} benchmark {b.get('weight')} x {b.get('reps')}: {err} (L-1, L-2)") from None
            src = f"{_fmt(w)} x {r}"
            if cfg.get("require_logged") and b.get("logged") is not True:
                ctx.pending[lift] = e
                ctx.note(f"{lift}: {src} is not confirmed as tested (logged is not true), so week 1 is technique "
                         f"plus a benchmark triple ramped from its e1RM {_fmt(e)} {unit} (CT-RGO-14, W-1).")
                continue
            extra = ""
            if r == 1:
                extra = "; a single counts as the weight lifted, with no Epley inflation (L-2)"
            elif r > 8:
                extra = f"; L-2 prefers 2 to 8 reps (6 or fewer), so {r} reps is a weaker estimate"
            ctx.e1rms[lift] = e
            if ctx.engine != "531":
                why = _uncertain(b, ctx, lift)
                ctx.note(f"{lift}: e1RM {_fmt(e)} {unit} from {src} (L-1){extra}; the top-set ranges are built "
                         f"from it (CT-PLM-3)" + (f". Uncertain benchmark ({', '.join(why)}): consider a fresh "
                                                  "benchmark before this block" if why else "") + ".")
                continue
            reasons = ctx.tm85 + _uncertain(b, ctx, lift)
            pct = 0.85 if reasons else 0.90
            tm = loads.training_max(e, pct, ctx.step)
            ctx.tms[lift] = tm
            ctx.note(f"{lift}: e1RM {_fmt(e)} {unit} from {src} (L-1){extra}; TM {_pct(pct)}% = {_fmt(tm)} {unit} "
                     + (f"(L-3: {', '.join(reasons)})." if reasons else "(L-3 default, rounded up).")
                     + f" Step {_fmt(ctx.step)} {unit} (L-4).")
        elif b.get("estimate") is not None:
            try:
                est = float(b["estimate"])
                if est <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                raise DraftError(f"{lift}: estimate {b.get('estimate')!r} is not a positive number") from None
            ctx.pending[lift] = est
        else:
            missing.append(lift)
    if missing:
        raise DraftError(
            f"W-5: no benchmark for {', '.join(missing)}. Give a recent set of 2 to 8 reps (L-2), or, for a lift "
            f"with no set yet, an estimated e1RM such as {{\"{missing[0]}\": {{\"estimate\": <{unit}>}}}}: its "
            "week-1 benchmark session ramps from that estimate (W-1), never from a guess (G-11)")
    for lift, est in ctx.pending.items():
        if lift not in ctx.e1rms and not any(lift in n and "CT-RGO-14" in n for n in ctx.notes):
            ctx.note(f"{lift}: no benchmark, so week 1 is a W-1 benchmark session ramping from the estimated "
                     f"e1RM {_fmt(est)} {unit} (W-5).")
    if ctx.pending:
        ctx.note(f"W-5, IL-20: {', '.join(ctx.pending)} {'is' if len(ctx.pending) == 1 else 'are'} left out of weeks 2 "
                 "onward. Re-issue the whole block from the week-1 benchmark result (same file name) before the "
                 "lifter's first week-2 session.")


# --- rows ----------------------------------------------------------------------------------------

def _wave_rows(lift: str, wave_week: int, floor: bool, ctx: _Ctx) -> list[model.Row]:
    """L-5 wave, L-6/IL-17 warm-up on the first work row, L-16 rest, IL-30 RIR, L-13 AMRAP cue."""
    tm = ctx.tms[lift]
    rest = ctx.t.get("rest", {})
    amrap = ctx.t.get("amrap", {"rir": "1-2", "cue": None})
    rows = []
    wave = loads.wave531(tm, wave_week, ctx.step)
    for i, (pct, reps, load) in enumerate(wave):
        heavy = reps.rstrip("+") in ("1", "2", "3")
        row = model.Row(exercise=lift, role="main", sets=1, reps=reps, rir=PERCENT_RIR, load=load,
                        basis=f"{_pct(pct)}% TM",
                        rest=rest.get("main_heavy" if heavy else "main", "Rest 3 min"),
                        warmup=loads.warmup_note(tm, ctx.step, ctx.unit) if i == 0 else None,
                        progression="tm_wave")
        if i == len(wave) - 1:
            if floor:   # CT-NOV-1 and G-20: an AMRAP the floor rules out becomes a fixed set at the floor
                row.reps = reps.rstrip("+")
                row.cue = NOV_CUE
            else:
                row.role, row.rir, row.cue = "main_amrap", amrap["rir"], amrap.get("cue")
        rows.append(row)
    return rows


def _fsl_row(lift: str, wave_week: int, sets: int, ctx: _Ctx, warm: bool) -> model.Row:
    """L-14 FSL, or 531-2x's FSL-style second exposure (CT-PLO-1): sets x 5 at the week's first-set %."""
    tm = ctx.tms[lift]
    pct, reps, load, n = loads.fsl(tm, wave_week, ctx.step, sets=sets)
    return model.Row(exercise=lift, role="supplemental", sets=n, reps=reps, rir=PERCENT_RIR, load=load,
                     basis=f"FSL {_pct(pct)}% TM", rest=ctx.t.get("rest", {}).get("supplemental", "Rest 2 min"),
                     warmup=loads.warmup_note(tm, ctx.step, ctx.unit) if warm else None, progression="tm_wave")


def _benchmark_rows(lift: str, ctx: _Ctx) -> list[model.Row]:
    """W-1 benchmark session: the ramp as one per-set row, then one set of 3 to 5 at the lifter's own load."""
    est = ctx.pending[lift]
    ladder = loads.benchmark_ladder(est, ctx.step, ctx.unit)
    prog = "rpe_topset" if ctx.engine == "topset" else "tm_wave"
    set_reps = ctx.t.get("benchmark", {}).get("set_reps", "3-5")
    nov = bool(ctx.tm85)
    rir = "3-4" if nov else "1-2"
    rep_words = set_reps.replace("-", " to ")
    return [
        model.Row(exercise=lift, role="benchmark", sets=len(ladder),
                  reps=", ".join(str(r) for _, r, _ in ladder), rir=RAMP_RIR,
                  load=[l for _, _, l in ladder], basis="Benchmark ramp", rest="Rest 2 min", progression=prog),
        model.Row(exercise=lift, role="benchmark", sets=1, reps=set_reps, rir=rir, load=None,
                  basis="Benchmark set", rest="Rest 3 min",
                  cue=f"your own load for {rep_words} reps, {'3' if nov else '1 to 2'} left in the tank",
                  progression=prog),
    ]


def _a7(rir: str, name: str, ctx: _Ctx) -> str:
    """A-7, CT-HYP-3: a free-weight compound never gets a planned RIR 0; it stops at RIR 1."""
    lo, hi, rng = _rir_bounds(rir)
    if lo == 0 and _fw_compound(name):
        if name not in ctx.a7_bumped:
            ctx.a7_bumped.add(name)
            ctx.note(f"A-7, CT-HYP-3: {name} is a free-weight compound, so its RIR 0 sets stop at RIR 1.")
        return _rir_text(1, max(hi, 1), rng)
    return rir


def _slot_rows(spec: dict, name: str, reason: Optional[str], sets: int, reps: str, rir: str, ctx: _Ctx,
               *, amrap_ok: bool) -> list[model.Row]:
    load = 0 if _is_bodyweight(name) else spec.get("load")
    rir = _a7(rir, name, ctx)
    common = dict(exercise=name, role="accessory", reps=reps, load=load, basis=spec.get("basis"),
                  tempo=spec.get("tempo"), rest=spec.get("rest"), reason=reason, cue=spec.get("cue"),
                  progression=spec.get("progression", "double"))
    last = amrap_ok and spec.get("amrap_last_set") and sets >= 2 and not _fw_compound(name)
    if not last:
        return [model.Row(sets=sets, rir=rir, **common)]
    tail = dict(common, role="accessory_amrap", reps=f"{_top_of_range(reps)}+", cue=LAST_SET_CUE)
    return [model.Row(sets=sets - 1, rir=rir, **common), model.Row(sets=1, rir=LAST_SET_RIR, **tail)]


def _deload_warmup(lifts: list[str], ctx: _Ctx) -> Optional[str]:
    """IL-17: the L-7 deload's main-lift warm-up as one IL-28 segment on the day's first row."""
    parts = []
    for lift in lifts:
        if lift in ctx.tms:
            note = loads.warmup_note(ctx.tms[lift], ctx.step, ctx.unit)
            parts.append(f"{lift} {note[len('Warm-up '):]}")
    return "Warm-up: " + "; ".join(parts) if parts else None


def _extras(dspec: dict, week: dict, deload: bool) -> list[str]:
    by_week = dspec.get("extras_by_week", {})
    if str(week["week"]) in by_week:
        return list(by_week[str(week["week"])])
    if deload and "deload_extras" in dspec:
        return list(dspec["deload_extras"])
    return list(dspec.get("extras", []))


# --- engines -------------------------------------------------------------------------------------

def _build_531(layout: dict, ctx: _Ctx) -> list[model.Week]:
    t = ctx.t
    supp = layout["supplemental"] if "supplemental" in layout else t.get("supplemental")   # L-14
    first_loading = next(w["week"] for w in t["weeks"] if w["kind"] == "loading")
    weeks = []
    for wk in t["weeks"]:
        n, deload = wk["week"], wk["kind"] == "deload"
        floor = ctx.nov_floor and n in (1, 2) and not deload
        days = []
        for i, dspec in enumerate(layout["days"], start=1):
            rows: list[model.Row] = []
            extras = _extras(dspec, wk, deload)
            if not deload:
                for lift in dspec.get("main", []):
                    if lift in ctx.tms:
                        rows += _wave_rows(lift, wk["wave"], floor, ctx)
                        if supp:
                            rows.append(_fsl_row(lift, wk["wave"], supp["sets"], ctx, warm=False))
                    elif lift in ctx.pending and n == first_loading:
                        rows += _benchmark_rows(lift, ctx)
                for sec in dspec.get("second", []):
                    if sec["lift"] in ctx.tms:
                        rows.append(_fsl_row(sec["lift"], wk["wave"], sec["sets"], ctx, warm=True))
            else:
                warm = _deload_warmup(dspec.get("main", []), ctx)
                if warm:
                    extras.append(warm)
            rows += _accessories(dspec, wk, deload, floor, ctx)
            days.append(model.Day(day=i, label=dspec.get("label"), rows=rows, extras=extras))
        weeks.append(model.Week(week=n, deload=deload, days=days))
    for d in layout["days"]:
        for sec in d.get("second", []):
            if sec["lift"] in ctx.pending:
                ctx.note(f"{sec['lift']}: its second exposure (CT-PLO-1) waits for the TM from the week-1 benchmark.")
    return weeks


def _accessories(dspec: dict, wk: dict, deload: bool, floor: bool, ctx: _Ctx) -> list[model.Row]:
    """The day's slots for one week of a 531, fixed or rotation template (A-1, A-4, L-7, CT-NOV-1)."""
    rows = []
    for slot in dspec.get("slots", []):
        spec = _slot_spec(slot, ctx.ptype)
        if "weeks" in spec and wk["week"] not in spec["weeks"]:
            continue
        name, reason = _resolve(spec, ctx)
        sets = int(spec["sets"])
        reps = str(wk.get("reps") or spec["reps"]) if ctx.engine == "rotation" else str(spec["reps"])
        rir = str(wk.get("rir") if ctx.engine == "rotation" else spec["rir"])
        if deload:
            sets, rir = loads.deload_accessory(sets, rir)   # L-7 {M4}: 30 to 50% fewer sets, RIR + 1, at least 3
            rows += _slot_rows(spec, name, reason, sets, reps, rir, ctx, amrap_ok=False)
            continue
        if floor:
            rir = _floor_rir(rir, NOV_FLOOR)
        rows += _slot_rows(spec, name, reason, sets, reps, rir, ctx, amrap_ok=not floor)
    return rows


def _build_fixed(layout: dict, ctx: _Ctx) -> list[model.Week]:
    weeks = []
    for wk in ctx.t["weeks"]:
        n, deload = wk["week"], wk["kind"] == "deload"
        floor = ctx.nov_floor and n in (1, 2) and not deload
        days = [model.Day(day=i, label=d.get("label"), extras=_extras(d, wk, deload),
                          rows=_accessories(d, wk, deload, floor, ctx))
                for i, d in enumerate(layout["days"], start=1)]
        weeks.append(model.Week(week=n, deload=deload, days=days))
    return weeks


def _chart_pct(reps, rpe) -> Decimal:
    """The RPE chart CT-PLM-3 asks for: L-1's Epley inverted at reps + RIR (RIR = 10 - RPE)."""
    to_failure = Decimal(str(reps)) + Decimal(10) - Decimal(str(rpe))
    return Decimal(1) / (Decimal(1) + loads.EPLEY * to_failure)


def _times(x, pct) -> float:
    return float(Decimal(repr(float(x))) * Decimal(pct))


def _rpe_mid(rpe_text: str) -> float:
    vals = [float(v) for v in str(rpe_text).split("-")]
    return sum(vals) / len(vals)


def _build_topset(layout: dict, phase: dict, ctx: _Ctx) -> list[model.Week]:
    """CT-PLM: top-set range + RPE as RIR, back-downs at a fixed fraction, a deload or an OPENER week."""
    t = ctx.t
    unit, step = ctx.unit, ctx.step
    rest = t.get("rest", {})
    bd = phase["backdown"]
    loading = [w for w in phase["weeks"] if w["kind"] == "loading"]
    lifts = [l for d in layout["days"] for l in d.get("topsets", [])]

    def chart(lift, k):   # the chart fraction for loading week k (1-based): that week's reps at its RPE target
        rpe = _rpe_mid(loads.topset_rpe(k, start=phase["rpe_start"], peak=phase["peak"]))
        return _chart_pct(loading[k - 1]["reps"][lift], rpe)

    # CT-PLM-3: week 1 centred on the chart load; later weeks add the weekly step to the midpoint. The step is
    # the chart's rise from the first to the last loading week, spread evenly and rounded up to the load step
    # (L-4), capped at the template's step, so a lighter lifter's range still holds the load its RPE target gives.
    mids: dict[str, dict[int, float]] = {}
    for lift in lifts:
        if lift not in ctx.e1rms:
            continue
        e = ctx.e1rms[lift]
        lo, hi = loads.topset_range(_times(e, chart(lift, 1)), lift, unit)
        mid0 = (lo + hi) / 2
        cap = loads.convert_kg(t["weekly_step_kg"][lift], unit)
        step_w = 0.0
        if len(loading) > 1:
            rise = _times(e, (chart(lift, len(loading)) - chart(lift, 1)) / (len(loading) - 1))
            step_w = min(cap, loads.round_up(rise, loads.step_for(unit))) if rise > 0 else 0.0
        mids[lift] = {w["week"]: mid0 + step_w * k for k, w in enumerate(loading)}
        ctx.note(f"{lift}: week-1 top-set midpoint {_fmt(mid0)} {unit} from e1RM {_fmt(e)} at "
                 f"{loading[0]['reps'][lift]} reps, RPE {loads.topset_rpe(1, start=phase['rpe_start'], peak=phase['peak'])} "
                 f"on the chart; +{_fmt(step_w)} {unit} a week (CT-PLM-3, cap {_fmt(cap)} {unit}).")

    variant = t.get("variant") if any(d.get("variant") for d in layout["days"]) else None
    held = phase.get("opener", {}).get("held_back", {})
    acc_weeks = phase.get("accessory_weeks")
    last_variant_load = None
    weeks = []
    for k, wk in enumerate(phase["weeks"]):
        n, kind = wk["week"], wk["kind"]
        deload = kind == "deload"
        floor = ctx.nov_floor and n in (1, 2) and kind == "loading"
        loading_idx = next((j + 1 for j, w in enumerate(loading) if w["week"] == n), None)
        days = []
        for i, dspec in enumerate(layout["days"], start=1):
            rows: list[model.Row] = []
            for lift in dspec.get("topsets", []):
                if lift not in ctx.e1rms:
                    if lift in ctx.pending and loading_idx == 1:
                        rows += _benchmark_rows(lift, ctx)
                    continue
                if kind == "loading":
                    mid = mids[lift][n]
                    lo, hi = loads.topset_range(mid, lift, unit)
                    rpe = loads.topset_rpe(loading_idx, start=phase["rpe_start"], peak=phase["peak"])
                    rir = loads.rpe_to_rir(rpe)   # CT-PLM-20
                    rows.append(model.Row(exercise=lift, role="topset", sets=1, reps=wk["reps"][lift],
                                          rir=_floor_rir(rir, NOV_FLOOR) if floor else rir, load=lo,
                                          basis=f"Top set {_fmt(lo)}-{_fmt(hi)}", rest=rest.get("topset", "Rest 3-5 min"),
                                          progression="rpe_topset"))
                    rows.append(model.Row(exercise=lift, role="backdown", sets=bd["sets"][lift], reps=bd["reps"],
                                          rir=bd.get("rir", PERCENT_RIR), load=loads.backdown(mid, bd["pct"], step),
                                          basis=f"{_pct(bd['pct'])}% of top set", rest=rest.get("backdown", "Rest 2 min"),
                                          progression="rpe_topset"))
                elif deload:
                    dl = phase["deload"]
                    load = loads.round_up(_times(ctx.e1rms[lift], _chart_pct(dl["reps"], dl["chart_rpe"])), step)
                    rows.append(model.Row(exercise=lift, role="supplemental", sets=dl["sets"], reps=dl["reps"],
                                          rir=loads.rpe_to_rir(dl["rpe"]), load=load,
                                          rest=rest.get("supplemental", "Rest 2 min"), progression="rpe_topset"))
                elif kind == "opener":
                    op = phase["opener"]
                    prev = mids[lift][loading[-1]["week"]]
                    rows.append(model.Row(exercise=lift, role="backdown", sets=op["backdown_sets"],
                                          reps=op["backdown_reps"], rir=PERCENT_RIR,
                                          load=loads.backdown(prev, op["backdown_pct_of_prev"], step),
                                          basis=f"{_pct(op['backdown_pct_of_prev'])}% of last week's top set",
                                          rest=rest.get("backdown", "Rest 2 min"), progression="rpe_topset"))
            if dspec.get("variant") and variant and variant["of"] in ctx.e1rms:
                of = variant["of"]
                if kind == "loading":
                    load = loads.backdown(mids[of][n], variant["pct"], step)
                    last_variant_load = load
                    rows.append(model.Row(exercise=variant["exercise"], role="supplemental", sets=variant["sets"],
                                          reps=wk["variant_reps"], rir=PERCENT_RIR, load=load,
                                          basis=f"{_pct(variant['pct'])}% of bench top set",
                                          rest=rest.get("supplemental", "Rest 2 min"), progression="rpe_topset"))
                elif deload and last_variant_load is not None:
                    dl = phase["deload"]
                    rows.append(model.Row(exercise=variant["exercise"], role="supplemental", sets=dl["variant_sets"],
                                          reps=dl["variant_reps"], rir=loads.rpe_to_rir(dl["rpe"]),
                                          load=loads.backdown(last_variant_load, dl["variant_pct"], step),
                                          rest=rest.get("supplemental", "Rest 2 min"), progression="rpe_topset"))
                elif kind == "opener":
                    op = phase["opener"]
                    prev = mids[of][loading[-1]["week"]]
                    rows.append(model.Row(exercise=variant["exercise"], role="supplemental", sets=variant["sets"],
                                          reps=wk["variant_reps"], rir=PERCENT_RIR,
                                          load=loads.backdown(prev, op["backdown_pct_of_prev"], step),
                                          basis=f"{_pct(op['backdown_pct_of_prev'])}% of last bench top set",
                                          rest=rest.get("supplemental", "Rest 2 min"), progression="rpe_topset"))
            if acc_weeks is None or n in acc_weeks:
                rows += _topset_accessories(dspec, loading_idx, deload, floor, ctx)
            days.append(model.Day(day=i, label=dspec.get("label"), rows=rows, extras=_extras(dspec, wk, deload)))
        weeks.append(model.Week(week=n, deload=deload, days=days))
    if held:
        ctx.note("CT-PLM-14, CT-PLM-20: week " + str(phase["weeks"][-1]["week"]) + "'s "
                 + ", ".join(f"{v} ({k})" for k, v in held.items())
                 + " singles are the lifter's to choose (the ironledger-meet-attempts skill); they are not rows yet. Add them, then re-issue the block under IL-20.")
    if variant and variant["of"] not in ctx.e1rms:
        ctx.note(f"{variant['exercise']} waits for the {variant['of']} e1RM from the week-1 benchmark.")
    return weeks


def _topset_accessories(dspec: dict, loading_idx, deload: bool, floor: bool, ctx: _Ctx) -> list[model.Row]:
    """CT-PLM-13 {M8}: accessory RIR steps down from the week-1 base; the deload is base + 1, at least 3."""
    rows = []
    for slot in dspec.get("slots", []):
        spec = _slot_spec(slot, ctx.ptype)
        name, reason = _resolve(spec, ctx)
        sets, base = int(spec["sets"]), spec["base_rir"]
        if deload:
            sets, _ = loads.deload_accessory(sets, "3")   # P-15: 30 to 50% fewer sets
            rir = loads.accessory_rir_plm(base, 1, deload=True)
        else:
            rir = loads.accessory_rir_plm(base, loading_idx)
            if floor:
                rir = _floor_rir(rir, NOV_FLOOR)
        rows += _slot_rows(spec, name, reason, sets, str(spec["reps"]), rir, ctx, amrap_ok=False)
    return rows


# --- checks on the result ----------------------------------------------------------------------

def _words(text: str) -> int:
    return sum(1 for tok in (text or "").split() if tok != "·")


def _fit_notes(program: model.Program, ctx: _Ctx) -> None:
    """VO-1: keep each day's first Notes cell at 20 words or fewer without losing anything compulsory.

    The first row carries the day's extras, and a deload day also carries the main-lift warm-ups (IL-17),
    so an A-8 reason there can overflow. The reason is never dropped (IL-14). First the day's optional
    label goes; then a row with no reason, basis or AMRAP partner moves to the front of that day.
    """
    from lib import ironledger_io as io

    def first_words(w, d):
        return _words(io.notes_for(program, w, d, d.rows[0], True, True))

    for w in program.weeks:
        for d in w.days:
            if not d.rows or first_words(w, d) <= NOTE_WORD_CAP:
                continue
            if d.label:
                ctx.note(f"VO-1: W{w.week} D{d.day} drops its label '{d.label}' from Notes to stay within 20 words.")
                d.label = None
            if first_words(w, d) <= NOTE_WORD_CAP:
                continue
            for j, r in enumerate(d.rows[1:], start=1):
                partner = j + 1 < len(d.rows) and d.rows[j + 1].exercise == r.exercise
                if r.role == "accessory" and not r.reason and not r.basis and not r.tempo and not partner:
                    d.rows.insert(0, d.rows.pop(j))
                    ctx.note(f"VO-1: W{w.week} D{d.day} leads with {r.exercise} so the reason on "
                             f"{d.rows[1].exercise} fits in its Notes.")
                    break


def _self_check(program: model.Program, ctx: _Ctx) -> None:
    """VO-1's 20 words, IL-6's equal day count and F-5's bar, reported now rather than first seen in pre-flight."""
    from lib import ironledger_io as io

    bar = loads.bar_weight(ctx.unit)
    under: dict[str, float] = {}
    for _, _, r in program.rows():
        if r.role in loads.COMPUTED_ROLES and library.is_barbell(r.exercise):
            for v in (r.load if isinstance(r.load, list) else [r.load]):
                if isinstance(v, (int, float)) and v < bar - 1e-9 and r.role != "benchmark":
                    under[r.exercise] = min(v, under.get(r.exercise, v))
    for lift, low in under.items():
        ctx.note(f"F-5: {lift} work sets go down to {_fmt(low)} {ctx.unit}, under the {_fmt(bar)} {ctx.unit} bar; "
                 "offer the lifter a dumbbell or technique-bar option.")
    rows = io.import_rows(program)[1:]
    for r in rows:
        words = _words(r[io.NOTES] or "")
        if words > NOTE_WORD_CAP:
            ctx.note(f"VO-1: W{r[io.WEEK]} {r[io.DAY]} {r[io.EXERCISE]} Notes run {words} words (cap {NOTE_WORD_CAP}); "
                     "shorten a reason or move that slot off the day's first row before pre-flight.")
    per_week: dict[int, set] = {}
    for r in rows:
        per_week.setdefault(r[io.WEEK], set()).add(r[io.DAY])
    if len({len(v) for v in per_week.values()}) > 1:
        ctx.note("IL-6: the import has a different number of days in some weeks; fix that before pre-flight.")


def _departures(t: dict, program: model.Program) -> list[dict]:
    """The template's rule-required departures that apply to this draft, plus IL-11 for a W-1 benchmark set (G-7)."""
    out = []
    roles = {r.role for _, _, r in program.rows()}
    for dep in t.get("departures", []):
        when = dep.get("when", "always")
        if when == "always" or when in roles:
            out.append({"rule": dep["rule"], "reason": dep["reason"]})
    if any(r.role == "benchmark" and r.load is None for _, _, r in program.rows()):
        out.append({"rule": "IL-11", "reason": "W-1, W-5: the benchmark set's load is the lifter's own choice after "
                                               "the ramp, so its Load is blank and raises IronLedger's one tolerated "
                                               "'No load given' warning; never a guessed load (G-11)"})
    return out


# --- the entry point ---------------------------------------------------------------------------

def generate(template_id: str, profile: model.Profile, benchmarks: Optional[dict], *, block: int = 1,
             choices: Optional[dict] = None, days: Optional[int] = None,
             phase: Optional[str] = None) -> tuple[model.Program, list[str]]:
    """Generate a complete designer-program/1 draft. Raises DraftError, naming the rule, when it can't."""
    return _generate(template_id, profile, benchmarks, block=block, choices=choices, days=days, phase=phase)


def generate_one_off(template_id: str, profile: model.Profile, benchmarks: Optional[dict], *, block: int = 1,
                     choices: Optional[dict] = None,
                     days: Optional[int] = None) -> tuple[model.Program, model.Program, list[str]]:
    """OO-1 to OO-6: two 4-week blocks, drafted together. Raises DraftError, naming the rule."""
    if template_id not in ONE_OFF_TEMPLATES:
        why = ONE_OFF_REFUSED.get(template_id, "it isn't on the two-block list")
        raise DraftError(f"OO-2: two blocks at once are drafted on {', '.join(ONE_OFF_TEMPLATES)}. {template_id} "
                         f"is refused: {why}. Draft one block at a time instead")
    weeks = len(load_template(template_id).get("weeks", []))
    if weeks != 4:
        raise DraftError(f"OO-1: {template_id} has {weeks}-week blocks; a two-block program is two 4-week blocks")

    a, notes_a = _generate(template_id, profile, benchmarks, block=block, choices=choices, days=days, part=1)
    carry, lines = None, []
    if a.tms:   # OO-4 {M28}: L-9's standard increment, as if every AMRAP met its minimum
        carry = {"tms": {}, "e1rms": dict(a.e1rms)}
        for lift, tm in a.tms.items():
            inc = loads.tm_increment(lift, a.unit)
            carry["tms"][lift] = float(Decimal(repr(float(tm))) + Decimal(repr(inc)))
            lines.append(f"{lift} {_fmt(tm)} + {_fmt(inc)} = {_fmt(carry['tms'][lift])} {a.unit}")
    b, notes_b = _generate(template_id, profile, benchmarks, block=block + 1, choices=choices, days=days,
                           part=2, carry=carry)

    blocks = [block, block + 1]
    a.one_off = {"part": 1, "of": 2, "blocks": blocks}
    self_check: dict[str, dict] = {}
    for w, _, r in a.rows():
        if r.role == "main_amrap" and not w.deload:
            load = r.load[-1] if isinstance(r.load, list) else r.load
            entry = self_check.setdefault(r.exercise, {
                "tm_block1": a.tms.get(r.exercise), "tm": b.tms.get(r.exercise),
                "increment": loads.tm_increment(r.exercise, a.unit), "amraps": []})
            entry["amraps"].append({"week": w.week, "min_reps": int(str(r.reps).rstrip("+")), "load": load})
    b.one_off = {"part": 2, "of": 2, "blocks": blocks, "self_check": self_check}

    notes = [f"Block {block}: {n}" for n in notes_a] + [f"Block {block + 1}: {n}" for n in notes_b if n not in notes_a]
    if lines:
        notes.append(f"OO-4 {{M28}}: block {block + 1}'s TMs are block {block}'s plus the L-9 increment ("
                     + "; ".join(lines) + f"). A lift with any block {block} AMRAP under its minimum repeats its "
                     f"block {block} loads; the hand-over tells the lifter so (OO-5).")
    else:
        notes.append(f"OO-6: block {block + 1} repeats the layout, and the lifter carries on from their own "
                     f"block {block} loads under A-6.")
    return a, b, notes


def _generate(template_id: str, profile: model.Profile, benchmarks: Optional[dict], *, block: int = 1,
              choices: Optional[dict] = None, days: Optional[int] = None, phase: Optional[str] = None,
              part: Optional[int] = None, carry: Optional[dict] = None) -> tuple[model.Program, list[str]]:
    """generate(), plus a one-off's part (1 or 2) and, for part 2, the TMs carried from part 1 (OO-4)."""
    t = load_template(template_id)
    _gate(t, profile)
    notes: list[str] = []
    ptype = _primary_type(t, profile, notes)
    unit = str(profile.unit or "kg").strip().lower()
    try:
        step = loads.step_for(unit, profile.microplates)
    except ValueError as err:
        raise DraftError(str(err)) from None
    if not isinstance(block, int) or isinstance(block, bool) or block < 1:
        raise DraftError(f"block {block!r} must be a whole number from 1 (IL-2)")

    ctx = _Ctx(t=t, profile=profile, block=block, unit=unit, step=step, ptype=ptype, engine=t["engine"], notes=notes)

    if t.get("min_available_days") and (profile.days is None or profile.days < t["min_available_days"]):
        raise DraftError(f"CT-HYP-6: {t['id']} is offered only with {t['min_available_days']} or more available days "
                         f"(the profile has {profile.days}); use 531-4day with hard-set accessories (CT-HYP-2)")
    if profile.session_min is not None and profile.session_min < 45:
        raise DraftError(f"CT-SEL-7: sessions of {profile.session_min} min use CT-GEN-3's time-minimum plan, which has "
                         "no template yet; ask the lifter for longer sessions or fewer exercises")
    layout, n_days = _pick_layout(t, profile, days, notes)

    kit = {str(e) for e in profile.equipment}
    if kit:
        missing = [e for e in t.get("equipment_required", []) if e not in kit]
        if missing:
            raise DraftError(f"CT-SEL-8: {t['id']} needs {', '.join(missing)}, which the profile doesn't list; "
                             "the lifter goes to pt-general")
    elif t.get("equipment_required"):
        notes.append("G-11: the profile lists no equipment; the slot defaults assume a full gym. Confirm it.")
    if t.get("equipment_ceiling"):     # CT-RGO-15 caps the profile (G-15), never widens it
        ceiling = set(t["equipment_ceiling"])
        ctx.avail = (ceiling & kit if kit else ceiling) | ALWAYS_AVAILABLE
    elif kit:
        ctx.avail = kit | ALWAYS_AVAILABLE

    status = str(profile.training_status or "").strip().lower()
    mods = {str(m).strip().upper() for m in profile.modifiers}
    returning = "returning" in _lower(profile.flags)
    if status == "novice":
        ctx.tm85.append("novice lifter")
    elif "NOV" in mods or returning:
        ctx.tm85.append("returning or NOV-modifier lifter")
    ctx.nov_floor = (block == 1 and (status == "novice" or "NOV" in mods)) or returning
    if part == 2:
        ctx.nov_floor = False   # OO-6: CT-NOV-1's floor is block 1's; block 2 follows 4 weeks of it
    if ctx.nov_floor:
        notes.append("CT-NOV-1: weeks 1 and 2 stop every set at RIR 3 or more, so the AMRAPs become fixed sets at "
                     "that floor and AMRAP Last Set rows wait for week 3 (G-20).")

    if phase is not None and t["engine"] != "topset":
        raise DraftError(f"template {t['id']} has no phases; phase applies to topset-backdown only")
    ph, phase_name = None, None
    if t["engine"] == "topset":
        phase_name = phase or "prep2"
        if phase_name not in t["phases"]:
            raise DraftError(f"topset-backdown phase {phase_name!r} unknown; use {' or '.join(t['phases'])}")
        ph = t["phases"][phase_name]
        notes.append(f"CT-PLM-6: phase {ph['name']}.")

    lifts = _required_lifts(t, layout)
    if t["engine"] in ("531", "topset"):
        if t["engine"] == "531" and status == "novice" and ptype in ("GEN", "HYP"):
            bad = [l for l in lifts if not _measured((benchmarks or {}).get(l))]
            if n_days < 3 or bad:
                raise DraftError("CT-NOV-2: a GEN or HYP novice uses 5/3/1 only with a measured 2 to 8-rep benchmark on "
                                 "each main lift and at least 3 days" + (f" (missing for {', '.join(bad)})" if bad else "")
                                 + "; start them on pt-general")
        if part == 2 and carry:   # OO-4: block 1's TMs plus the L-9 increment, worked out by generate_one_off
            ctx.tms, ctx.e1rms = dict(carry["tms"]), dict(carry["e1rms"])
        else:
            _benchmarks(lifts, benchmarks or {}, ctx)
        if part == 1 and ctx.pending:
            raise DraftError(f"OO-3: two blocks at once can't start {', '.join(ctx.pending)} with a week-1 benchmark session, "
                             "because block 2 is written before week 1 is trained (W-5, IL-20). Ask the lifter for a recent "
                             "set of 2 to 8 reps for each (L-2, G-11), draft one block, or draft pt-general")
        if phase_name == "peak" and ctx.pending:
            raise DraftError(f"CT-PLM-3: PEAK builds on the e1RMs PREP 2 produced; {', '.join(ctx.pending)} "
                             "has no benchmark. Benchmark it first, or draft PREP 2")
    elif benchmarks:
        notes.append(f"{t['id']} prescribes no computed loads (double progression, A-6); the benchmarks weren't used.")

    _check_choices(choices, layout, ctx)

    if t["engine"] == "531":
        weeks = _build_531(layout, ctx)
    elif t["engine"] == "topset":
        weeks = _build_topset(layout, ph, ctx)
    else:
        weeks = _build_fixed(layout, ctx)

    decisions = list(dict.fromkeys(t["decisions_relied_on"] + t.get("decisions_by_type", {}).get(ptype, [])
                                   + (["M28"] if part and ctx.tms else [])))
    decisions.sort(key=lambda m: int(re.sub(r"\D", "", m) or 0))
    program = model.Program(client=profile.client, client_name=(profile.name or "").strip() or None,
                            block=block, unit=unit, template=t["id"], primary_type=ptype,
                            modifiers=list(profile.modifiers), tms=dict(ctx.tms), e1rms=dict(ctx.e1rms),
                            decisions_relied_on=decisions, weeks=weeks)
    program.departures = _departures(t, program)
    for dep in program.departures:
        ctx.note(f"Departure from {dep['rule']}: {dep['reason']}.")
    for line in t.get("notes", []) + t.get("notes_by_type", {}).get(ptype, []) + (ph or {}).get("notes", []):
        ctx.note(line)
    _fit_notes(program, ctx)
    _self_check(program, ctx)
    return program, ctx.notes

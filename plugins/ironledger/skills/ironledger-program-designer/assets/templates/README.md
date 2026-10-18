# Program templates

The programs as data. `scripts/lib/draft.py` turns a template, a lifter's profile, their benchmark sets and the skill's slot choices into a complete `designer-program/1` draft. The skill chooses the template and the accessory slots. Every number comes from `draft.py` and `lib.loads` (rulebook G-6).

```python
from lib import draft
program, notes = draft.generate(template_id, profile, benchmarks, block=1, choices=None, days=None, phase=None)
```

SKILL.md's `designer.py draft TEMPLATE profile.json benchmarks.json [--choices …] [--days N] --block N` command is a thin wrapper around this call.

## The templates

| id | Lifter types | Default days | Layouts | Engine |
|---|---|---|---|---|
| `531-4day` | GEN, HYP | 4 | 4, 3, 2 (CT-GEN-2) | 5/3/1 + FSL (none on 2 and 3 days, L-14) |
| `531-2x` | PLO, GEN | 4 | 4 | 5/3/1 + an FSL-style second exposure of squat, bench and deadlift (CT-PLO-1, M1) |
| `531-club` | RGO | 3 | 3, 2 (CT-RGO-2), 4 | 5/3/1, club equipment only, Limber 11 |
| `pt-general` | PT, GEN, HYP (and any type without a barbell kit, CT-SEL-8) | 3 | 3, 2, 4 | fixed slots, double progression |
| `hypertrophy-rotation` | HYP, 5 or more available days | 3 | 3 (one rotation per Week) | Rep phases (CT-HYP-1) |
| `topset-backdown` | PLM | 4 | 4 | top set + back-downs; phases `prep2` and `peak` |
| `adf-prep` | ADF | 5 | 5, 6 | 5/3/1 strength days + 3 run days as IL-28 extras |

There is no `pl-macrocycle` template (method decision M10).

A layout exists only where the rules give one. Asking for a day count a template has no layout for, or more days than `profile.days`, raises `DraftError` (CT-SEL-7).

## Inputs

**benchmarks.json** `{lift: {"weight", "reps", "rir"?, "age_weeks"?, "logged"?}}`

* e1RM is L-1 (`loads.e1rm`); more than 10 reps is refused (L-2).
* TM is 90% of e1RM, or 85% for a novice, NOV-modifier or `returning`-flagged lifter, or for an uncertain benchmark: older than 8 weeks, `logged: false`, or `rir` 3 or more (L-3). The notes show each TM with its inputs.
* A lift with no set yet takes `{"estimate": <e1RM>}`. Week 1 gets a W-1 benchmark session ramped from that estimate: one `benchmark` row with the ramp as per-set lists, then one benchmark set at the lifter's own load (blank Load, recorded as an IL-11 departure). The lift is left out of weeks 2 onward, and the notes say to re-issue the block under IL-20 (W-5). A lift with neither a set nor an estimate is refused, with every missing lift listed once (G-11).
* `531-club` counts a set only when `logged` is true (CT-RGO-14). Otherwise the reported set's e1RM seeds a week-1 ramp to a heavy triple.
* `pt-general` and `hypertrophy-rotation` compute no loads and ignore benchmarks.

**choices.json** `{slot_id: "Exercise"}` or `{slot_id: {"exercise": "...", "reason": "..."}}`

* The slot ids are those of the layout in use. An unknown id is refused.
* The exercise must be a library name or an approved alias (`library.known`). It must not be on `profile.dislikes` or `profile.avoid` (A-8, G-15), and it must fit the lifter's equipment (or the club's). Anything else is refused.
* `reason` goes into Notes on that slot's rows. It is compulsory for an injury- or dislike-driven swap (A-8, VO-4). When a default on the dislike or avoid list is replaced without a reason, the generator writes one.
* A slot's sets, reps, RIR, basis and progression stay the template's. For a timed or distance slot (`Reps in seconds`, `Reps in metres`), choose an exercise done the same way.

Without a choice, a slot takes its default, or else the first alternative that is known, not disliked or avoided, and fits the equipment. Each fallback is listed in the notes.

## File schema (`designer-template/1`)

```jsonc
{
  "schema": "designer-template/1",
  "id": "531-4day",                       // the file name without .json
  "name": "...",
  "engine": "531" | "topset" | "rotation" | "fixed",
  "client_types": ["GEN", "HYP"],         // CT-SEL-1 primary types this template serves
  "any_type_without": ["barbell", ...],   // optional: any type may use it when the profile lacks these (CT-SEL-8)
  "default_days": 4,
  "min_available_days": 5,                // optional: profile.days must reach this (CT-HYP-6)
  "rules": ["L-5", ...],                  // the rule ids the template implements (documentation)
  "decisions_relied_on": ["M1", ...],     // copied to program.decisions_relied_on (F-9)
  "decisions_by_type": {"HYP": ["M14"]},  // optional additions for one primary type
  "equipment_required": ["barbell", "rack", "bench"],  // library equipment vocabulary (CT-SEL-8)
  "equipment_ceiling": [...],             // optional: the only equipment slots may use (CT-RGO-15)
  "weeks": [                              // not used by the topset engine, which has phases
    {"week": 1, "kind": "loading", "wave": 1},        // 531: wave week 1-3 (L-5)
    {"week": 4, "kind": "deload"},                    // L-7
    {"week": 1, "kind": "loading", "reps": "13-15", "rir": "3"}   // rotation: the phase's reps and RIR
  ],
  "rest": {"main": "Rest 3 min", "main_heavy": "Rest 3-5 min", "supplemental": "Rest 2 min",
           "topset": "Rest 3-5 min", "backdown": "Rest 2 min"},   // IL-14 rest tokens (L-16)
  "amrap": {"rir": "1-2", "cue": "..."},  // the 5/3/1 AMRAP row's RIR cell and cue (IL-30, L-13, CT-RGO-13)
  "supplemental": {"type": "fsl", "sets": 5} | null,   // L-14; a layout may override it
  "benchmark": {"require_logged": true, "set_reps": "3"},   // optional W-1 settings
  "departures": [{"rule": "IL-30", "when": "main_amrap" | "always", "reason": "..."}],  // rules the template must depart from, with G-20's reason
  "layouts": {
    "4": {
      "source": "...",                     // where the layout comes from
      "supplemental": null,                // optional override
      "days": [
        {
          "label": "Squat",                // optional; goes to Notes as "Day: Squat" (IL-6, IL-14)
          "extras": ["Warm-up: knee mobility", "Then: neck isometrics"],   // IL-28 segments
          "deload_extras": ["Warm-up: Limber 11"],     // optional: the deload week's extras
          "extras_by_week": {"4": ["..."]},            // optional: one week's extras
          "main": ["Squat"],               // 531 engine: 5/3/1 lifts, in order (P-16)
          "second": [{"lift": "Bench Press", "sets": 5}],   // 531-2x: FSL-style second exposures
          "topsets": ["Squat"],            // topset engine: top set + back-downs
          "variant": true,                 // topset engine: the template's variant lift (close-grip bench)
          "slots": [ ... ]                 // accessories, in session order (A-1)
        }
      ]
    }
  },
  "phases": { "prep2": {...}, "peak": {...} },   // topset engine only, see below
  "notes": ["..."],                       // review-page lines returned with every draft
  "notes_by_type": {"HYP": ["..."]}       // lines for one primary type
}
```

A day with no `main`, `topsets`, `variant` or `slots` holds only IL-28 extras: an ADF run day, for example. It takes no Day number in the import, but it counts toward the lifter's days (CT-SEL-7).

### Slots

```jsonc
{
  "id": "bench.delts",                     // unique within the layout; the key for choices
  "pattern": "shoulder-abduction",         // movement-pattern tag
  "kind": "compound" | "isolation" | "core" | "carry",
  "exercise": "Lateral Raise",             // the default: an exact library name (LB-1)
  "alternatives": ["Cable Lateral Raise"], // used in order when the default can't be (equipment, dislike, avoid)
  "sets": 3, "reps": "12-15", "rir": "2-3",   // IL-9 and IL-12 forms; rotation slots take reps and RIR from the week
  "base_rir": 1,                           // topset engine: the CT-PLM-13 week-1 base
  "progression": "double",                 // P-13; the default is double
  "amrap_last_set": true,                  // A-3: the last set becomes its own "15+" row at RIR 0-1 (IL-30)
  "basis": "Reps in seconds",              // IL-28 timed or distance work
  "tempo": "Full ROM", "rest": "Rest 2 min", "cue": "...",
  "load": null,                            // optional; bodyweight exercises are written as 0 (IL-10)
  "weeks": [1, 2],                         // optional: only these weeks
  "by_type": {"HYP": {"exercise": "Hack Squat", "sets": 2, "reps": "6-10", "rir": "0"}}   // overrides for one primary type
}
```

The generator also applies these rules to every slot:
* **A-7, CT-HYP-3:** a planned RIR 0 on a free-weight compound becomes RIR 1. An AMRAP Last Set is never put on one.
* **CT-NOV-1:** in a novice's or NOV lifter's first block, and in any block for a `returning` lifter, weeks 1 and 2 hold every set at RIR 3 or more. The 5/3/1 AMRAP becomes a fixed set at that floor, and AMRAP Last Set rows wait for week 3 (G-20).
* **L-7:** in the deload week, `loads.deload_accessory` gives 30 to 50% fewer sets at RIR + 1 (at least 3), with no AMRAP rows. The main lift keeps only its warm-up, as one IL-28 segment. On a two-lift day both warm-ups share that segment.

### topset-backdown phases

`phase="prep2"` (the default) is 4 loading weeks plus a deload. `phase="peak"` is 3 loading weeks plus the OPENER week, generated as its own block from the e1RMs PREP 2 produced (CT-PLM-6). Each phase gives:

* `weeks`: `kind` is `loading`, `deload` or `opener`, with `reps` per lift and `variant_reps`.
* `rpe_start` and `peak`: the RPE target comes from `loads.topset_rpe`, written as RIR by `loads.rpe_to_rir` (CT-PLM-5, CT-PLM-20).
* `backdown`: `pct` (CT-PLM-4), `reps`, `sets` per lift and `rir`.
* `deload`: sets and reps at an RPE range, with the load from the chart at `chart_rpe` (CT-PLM-6).
* `opener`: the held-back lifts and the OPENER-week back-down fraction.
* `accessory_weeks` (optional): CT-PLM-11.

Week 1's range is centred on the chart load, which is L-1's Epley inverted at reps + (10 − RPE), through `loads.topset_range`. Later weeks add a weekly step: the chart's rise from the first to the last loading week, rounded up to the load step and capped at `weekly_step_kg` (CT-PLM-3). The top set's Load is the low end of its range, with `Top set <low>-<high>` in Notes (CT-PLM-20). OPENER and SECOND singles are left out of the rows until the lifter chooses them (the ironledger-meet-attempts skill), and the notes say so (CT-PLM-14).

## Checking a template

`draft.validate_template(t)` lists unknown names, duplicate slot ids and layouts whose day count doesn't match their key. The repository's `tests/program_designer/test_draft.py` runs it on every file. For every template and layout, it also generates a draft and requires pre-flight with no `fail`; with `IRONLEDGER_LIVE=1` it checks each written import with the live IronLedger program file checker.

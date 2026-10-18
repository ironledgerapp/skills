---
name: ironledger-program-designer
description: Design a complete strength training block for a lifter from their goal, experience, schedule, equipment and recent sets, using evidence-based programming rules and tested templates (5/3/1 variants, powerlifting meet prep, hypertrophy, general and injury-aware training, rugby and ADF preparation), then write it as an IronLedger import file checked with the app's own import rules. Use when a lifter wants a program built for them. For writing up a program they already have, use ironledger-program-writer instead.
---

# Design a program for IronLedger

This skill chooses the program, not just the file format. It picks a template for the lifter's type and goal, works out every load, checks the draft against a rulebook of programming rules, and writes an IronLedger import file. **The lifter decides** (G-1): present the draft, the alternative and the reasons, never a single "best" answer.

Everything that must be right every time lives in the scripts and reference files: the maths, the rules and the file format. Your job is the judgement in between: asking the right questions, choosing the template and its alternative, choosing accessories, and explaining why. **Every number comes from `scripts/designer.py`. Never calculate a load, e1RM or volume in prose (G-6).**

The scripts need Python 3.9 or later and nothing else.

## 0. Before anything else

**Screen (G-4).** Ask these six questions exactly as written. They are Stage 1 of the Adult Pre-Exercise Screening System (APSS V2, Exercise & Sport Science Australia, Fitness Australia and Sports Medicine Australia), which says this stage "may be self-administered and self-evaluated":

1. Has your medical practitioner ever told you that you have a heart condition or have you ever suffered a stroke?
2. Do you ever experience unexplained pains or discomfort in your chest at rest or during physical activity/exercise?
3. Do you ever feel faint, dizzy or lose balance during physical activity/exercise?
4. Have you had an asthma attack requiring immediate medical attention at any time over the last 12 months?
5. If you have diabetes (type 1 or 2) have you had trouble controlling your blood sugar (glucose) in the last 3 months?
6. Do you have any other conditions that may require special consideration for you to exercise?

A yes to any of them: the APSS says to "seek guidance from an appropriate allied health professional or medical practitioner prior to undertaking exercise". Draft nothing until the lifter has that guidance. Set `screen_cleared` to true only on six noes or the professional's go-ahead.

**Under 18 (CT-JUN-1).** Draft nothing. Heavy lifting for under-18s needs a qualified coach's supervision (CT-JUN-3), which a self-serve program can't provide.

**Red flags (G-9).** If the lifter mentions chest pain, fainting, new numbness, bladder or bowel changes with back pain, a suspected fracture, concussion, signs of disordered eating, or thoughts of self-harm, stop and follow the pathway in `references/rulebook.md` RF-5 to RF-18 before anything else. Never diagnose (G-10).

## 1. Files

**Script:** run it from the skill directory: `python3 scripts/designer.py <command> …`

| Command | Use |
|---|---|
| `loads e1rm --weight W --reps R [--unit kg\|lb] [--microplates]` | e1RM, TM at 90% and 85%, and `app_e1rm`, the whole-number e1RM the IronLedger app displays |
| `loads wave --tm T --week N` / `loads warmup --tm T` | a 5/3/1 week, and its warm-up |
| `loads next-tm --lift L --tm T --amraps FILE.json [--prior E1,E2]` | the next cycle's TM under L-9, L-10 and L-11 |
| `normalize "NAME"` | maps a name as people write it to the IronLedger library name (exact or synonym only, never a guess) |
| `subs PATTERN_OR_NAME --profile profile.json [--tags knee-friendly]` | allowed substitutes for the lifter's equipment, dislikes and avoid list |
| `draft TEMPLATE profile.json benchmarks.json [--choices choices.json] [--days N] [--phase prep2\|peak] --block N --out program.json` | generates the whole block from the template |
| `draft TEMPLATE profile.json benchmarks.json [--choices …] [--days N] --two-blocks --block N --out DIR` | an 8-week program: blocks N and N+1 together, into `DIR/Block N/` and `DIR/Block N+1/` (rulebook OO) |
| `preflight program.json profile.json [--csv FILE]` | every rule check; exit 1 means fix it before the lifter sees it |
| `build program.json --out DIR` | the IronLedger import file, `IronLedger Block <N>.csv` |
| `volume program.json` | weekly fractional hard sets per muscle |

**References**, read as needed:

| File | Read it when |
|---|---|
| `references/rulebook.md` | always: G (ground rules), RF (red flags), F (format), L (5/3/1 engine), A (accessories), P (general evidence rules), W (measurement), OO (two blocks at once) |
| `references/client-types.md` | choosing the lifter type and template (CT-SEL), and each type's rules |
| `references/voice.md` | writing Notes and the hand-over |
| `references/ironledger-import.md` | the import file, exercise names, and the setup steps for the lifter (ON) |
| `references/evidence.md` | before citing research. **Cite only PMIDs listed there** (G-8). |

**Assets:** `assets/templates/*.json` (the programs as data), `assets/exercise-library.json` (IronLedger's 201 names), `assets/exercise-synonyms.json`, `assets/exercise-aliases.json` and `assets/substitutions.json`.

## 2. Design a block

1. **Ask once** (G-11), as a single list, for everything the draft needs and the lifter hasn't said:
   - goal, and any dated event (a meet, a rugby season, an ADF fitness assessment);
   - training age and recent breaks, sex and age;
   - days a week and minutes a session;
   - equipment (`barbell`, `rack`, `bench`, `dumbbell`, `cable`, `machine`, `kettlebell`, `ez_bar`, `pull_up_bar`, `dip_bars`, plus `trap_bar`, `landmine`, `ski_erg`, `air_bike`);
   - exercises they dislike, and anything an injury or a clinician rules out;
   - unit (kg or lb), and whether they own microplates;
   - a recent hard set for each main lift: weight, reps, reps in reserve, how many weeks ago, and whether they logged it.

   Never fill a gap with a guess.
2. **Profile.** Write `profile.json`:

   ```json
   {"schema": "designer-profile/1", "client": "Sam", "unit": "kg", "training_status": "intermediate",
    "days": 4, "session_min": 75, "equipment": ["barbell", "rack", "bench", "dumbbell", "cable", "machine"],
    "dislikes": [], "avoid": [], "primary_type": "GEN", "modifiers": [], "age_band": "adult",
    "screen_cleared": true, "flags": [], "goal": "stronger squat and deadlift", "target_date": null}
   ```

   `client` is any short label. Record conditions the lifter reports (for example `pregnancy`, `osteoporosis`) in `flags`.
3. **Type and template** (client-types.md CT-SEL-1 to CT-SEL-8). State the primary type, the modifiers, the template, **one alternative**, and the signal behind each choice. Templates: `531-4day`, `531-2x`, `531-club`, `topset-backdown`, `hypertrophy-rotation`, `pt-general`, `adf-prep`.
4. **Benchmarks.** Write `benchmarks.json` as `{lift: {"weight", "reps", "rir", "age_weeks", "logged"}}`, and show `loads e1rm` for each lift. A lift with no recent set takes `{"estimate": <e1RM>}` and gets a week-1 benchmark session (W-5). In that case, tell the lifter to come back after week 1 with the result, so the rest of the block can be re-issued.
5. **Accessory choices.** Start from the template's defaults. For every change, use `subs` to find an allowed replacement, and write `choices.json` as `{slot: {"exercise": …, "reason": …}}`. A reason is compulsory when the change is for an injury or a dislike (A-8). Use `normalize` for any name the lifter writes their own way.
6. **Generate:** `draft …`. Read its notes: the TM choices, missing benchmarks, and the method decisions relied on.
7. **Pre-flight:** `preflight program.json profile.json`. Fix every `fail` and run it again. Add a departure (`{"rule", "reason"}` in `program.departures`) only if a rule genuinely has to give under G-20, never just to make a check pass.
8. **Build and check the file:**
   - run `build program.json --out DIR`;
   - run `preflight program.json profile.json --csv "DIR/IronLedger Block <N>.csv"`;
   - call `check_program_file` on the IronLedger MCP server (`https://www.ironledger.app/mcp`), with the whole file as `file` and its name as `fileName`. Without MCP, POST the same JSON to `https://www.ironledger.app/api/tools/program-file`.

   The file is ready only when IL-24 holds: `imports` is true, there are no `error` or `match` issues, and the only warnings are "No load given" on the accessory rows left for the lifter to choose.
9. **Hand it over.** Keep it short:
   - the template, the alternative and the signals;
   - each main lift's TM beside the set it came from;
   - the method decisions the draft relied on (preflight's F-9 line), and any departures or warnings;
   - each day's extras from `program.json` (warm-up blocks, runs, conditioning), which aren't rows in the file;
   - the pain rule (CT-PT-5);
   - the setup steps in `references/ironledger-import.md` ON-9, with the lifter's unit.

   Then give the file.
10. **Edits.** Apply any change the lifter asks for to `program.json`, never to the CSV, then run steps 7 and 8 again.

**An 8-week program in one go** (`--two-blocks`, rulebook OO): for a lifter who won't come back after week 1. Only `531-4day`, `531-2x`, `531-club`, `adf-prep` and `pt-general` qualify. Every main lift needs a real benchmark set. Block 2's TMs are block 1's plus the standard increment. Tell the lifter the check in block 2's `program.json` (`one_off.self_check`): any main lift with a block 1 AMRAP below its minimum repeats its block 1 loads through block 2 (OO-4, OO-5).

## 3. The next block

1. Ask for the block's AMRAP sets for each main lift: weight, reps and minimum reps. They can read them from IronLedger's History CSV export; see the `ironledger-training-review` skill. Save them as `amraps-<lift>.json`: `[{"weight", "reps", "min_reps"}]`.
2. Run `loads next-tm --lift L --tm T --amraps amraps-<lift>.json --prior <earlier e1RMs>`. It applies L-9 (the standard increment), L-10 (a reset after 2 missed AMRAPs in a row) and L-11 (a bigger move only when 2 exposures agree). An AMRAP over 10 reps never moves a TM. Show its reasons.
3. Draft block N+1 with section 2 and `--block N+1`. Its file has a new name, so it imports as a new program (IL-23). Get it to the lifter before their last session of the current block (ON-6).

To revise the current block (for example after a week-1 benchmark), re-issue the whole block under the same file name. Weeks already trained are copied unchanged, and the lifter chooses Update in place when importing (IL-20).

## 4. Writing rules

- Plain English, short sentences, no em dashes, no emojis (voice.md).
- Effort is written as RIR, never RPE (A-5). A template's RPE is converted under CT-PLM-20.
- Rep ranges use an ASCII hyphen (`8-12`), never "to" or an en dash (F-3).
- Notes: one line, logistics first, at most one cue, and a reason for any injury- or dislike-driven choice (VO-1 to VO-4).

## 5. Never

These are the G rules; `rulebook.md` has them in full.

- Never present a single "recommended action" as the answer.
- Never diagnose, or give medical, physiotherapy or psychological advice.
- Never compute ACWR, injury-risk or readiness scores.
- Never flag on a single data point except for safety.
- Never override the lifter's documented constraints.
- Never invent data, exercises or citations.
- Never plan a weight cut. For a meet's attempts, use the `ironledger-meet-attempts` skill. For nutrition, use `ironledger-nutrition-plan`.

## 6. Method decisions

The rules tagged `{Mnn}` follow the recommended option of a method decision, listed at the top of `rulebook.md`. Preflight reports the ones each draft relied on, so the lifter can see which choices a program rests on.

---
name: ironledger-training-review
description: Review a lifter's training from IronLedger's own exports (the History CSV or the Export everything JSON backup), covering progress on each lift, records, volume, effort and consistency, and say what to change. Use when a lifter shares an IronLedger export and asks how their training is going, why a lift has stalled, or what to do next.
---

# Review training from an IronLedger export

IronLedger exports a lifter's history in two forms. Both work without any connection to IronLedger: the lifter attaches the file.

## The files

**History CSV.** In the app, open the History tab, tap CSV, choose a range and tap Export. The same CSV is also under Profile, then Account, then Export everything. It has one row per set, with these columns:

| Column | Meaning |
|---|---|
| Exported At | When the file was made |
| Date | When the session started (ISO time) |
| Program | The program the session came from |
| Session | The session's day number in the program |
| Exercise | Exercise name; blank on a skipped session's row |
| Set | Set number |
| Target Weight, Target Reps, Target RPE, Target RIR | What was prescribed or recommended |
| Actual Weight, Actual Reps, Actual RPE, Actual RIR | What was logged |
| Completed | `yes` or `no`. Only completed sets count |
| Completion Source | How the set was logged, for example accepted from the target or typed by hand; `skipped` marks a skipped session |
| Volume | Weight × reps, for completed sets only |
| Weight Unit | The app's unit when the file was exported |
| Set Notes, Session Notes | Free text |

**JSON backup.** Under Profile, then Account, tap Export everything and choose Everything as JSON. It is an object with:
- `schemaVersion`, `app`, `appVersion` and `exportedAt`;
- `sessions`, the full session records;
- `programs`, `personalRecords`, `customExercises` and `settings`.

The app can't import this backup; it's for reading and safekeeping.

## How to read them

- **Count only completed sets** (`Completed = yes`). The app's stats, records and recommendations ignore the rest, so the review should too.
- **Units:** use the lifter's unit. `Weight Unit` is the setting at export time. If they changed units, older sets may be in the other unit; JSON sets logged from app v1.9.1 on carry their own unit.
- **Estimated one-rep max:** IronLedger uses Epley, weight × (1 + reps ÷ 30), and a single counts as itself. Use the same formula so your numbers match the app's, and treat estimates from more than 10 reps as unreliable. The IronLedger MCP tool `one_rep_max` does this calculation.
- **Effort:** RPE is read as reps in reserve, so RPE 8 means about 2 reps left. Sets logged without RPE or RIR carry no effort information. Say so; don't guess.

## What a review covers

1. **Each main lift over time:** best estimated max per week, the top set, and whether it is rising, flat or falling. Name the comparison window.
2. **Records:** new bests in weight, reps at a weight, and estimated max.
3. **Volume:** completed sets per lift or muscle group per week, and big jumps or drops.
4. **Consistency:** sessions done against sessions planned, and skipped sessions (rows with `Completion Source = skipped`).
5. **What to change:** specific and tied to the data, such as a lift flat for three weeks at RPE 9, or volume doubled in one week. If the data can't answer a question, say what's missing.

## Be careful

- Describe only what the file shows. Don't invent sessions, lifts or numbers, and say how many weeks the file covers.
- An estimated max is a trend signal, not a promise of what the lifter can lift today.
- This is training guidance, not medical advice. Pain, injury or illness are for a professional.
- If the lifter wants a new program from the review, use the `ironledger-program-writer` skill to write it as a file the app imports.

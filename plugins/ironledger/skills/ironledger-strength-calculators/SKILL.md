---
name: ironledger-strength-calculators
description: Calculate one-rep max, RPE-based loads, barbell plate loading, warm-up sets, and DOTS, IPF GL and Wilks scores with IronLedger's free calculators, and check a training program file before it is imported into the IronLedger app. Use when a lifter asks what to load, what their max is, how to warm up, how a powerlifting total scores, or wants a program they can import into IronLedger.
---

# IronLedger strength calculators

Free, read-only calculators from IronLedger (https://www.ironledger.app). No account or API key.

## Ways to call them

- MCP: add https://www.ironledger.app/mcp as a remote MCP server (Streamable HTTP, no sign-in).
- HTTP: GET or POST https://www.ironledger.app/api/tools/<tool>. Described in https://www.ironledger.app/openapi.json.

## Tools

- `one_rep_max` (GET https://www.ironledger.app/api/tools/one-rep-max): Estimate a one-rep max (1RM) from a set of weight × reps, with a percentage table and the load each rep count should allow. Epley by default, Brzycki optional. Estimates above 10 reps are flagged as less reliable. Parameters: weight, reps, unit (optional), formula (optional).
- `rpe_estimate_max` (GET https://www.ironledger.app/api/tools/rpe-estimate-max): Estimate a one-rep max from weight, reps and RPE, treating RPE as reps in reserve (RPE 8 = 2 reps left) and applying the one-rep max formula to reps + reps in reserve. Parameters: weight, reps, rpe, unit (optional), formula (optional).
- `rpe_target_load` (GET https://www.ironledger.app/api/tools/rpe-target-load): Find the load for a set of a given number of reps at a target RPE, from a known or estimated one-rep max. Rounded to the nearest 0.5. Parameters: oneRepMax, reps, rpe, unit (optional), formula (optional).
- `plate_loading` (GET https://www.ironledger.app/api/tools/plates): Work out which plates to put on each side of a barbell to reach a target weight, using standard gym plates or the plates you list. Reports the exact load and anything your plates can’t make. Parameters: target, unit (optional), bar (optional), collars (optional), collarWeight (optional), plates (optional).
- `warmup_sets` (GET https://www.ironledger.app/api/tools/warm-up): Build a warm-up ramp to a working weight: plate-friendly jumps, reps falling from 10 to singles, with the plates for each set. The same ramp the IronLedger app suggests. Parameters: workingWeight, sets (optional), unit (optional), bar (optional).
- `powerlifting_score` (GET https://www.ironledger.app/api/tools/powerlifting-score): Score a powerlifting total (or a bench press) against bodyweight with DOTS, IPF GL points and the original Wilks, using the coefficients the OpenPowerlifting rankings use. Parameters: total, bodyweight, unit (optional), sex, equipment (optional), event (optional).
- `check_program_file` (GET https://www.ironledger.app/api/tools/program-file): Check a training program written as a CSV or TSV file exactly as the IronLedger app will import it, before anyone loads it on a phone. Returns the weeks, sessions and exercises it creates, every skipped row and warning with its row number, the exercise names the app will question ("Did you mean ...?"), and names that will become new custom exercises. Use it whenever you write a program for someone to import into IronLedger, and fix anything it reports first. The app names the program after the file, so pass the file name you will give it. Parameters: file, fileName (optional).

## Using the results

- Every response has `summary` (one sentence), `result` (the numbers), `method` (the formula) and `url` (the same result on ironledger.app, safe to share).
- Pass `unit` as kg or lb. Loads come back in the same unit.
- One-rep max estimates above 10 reps are flagged `reliable: false`; say so to the user.
- RPE is read as reps in reserve: RPE 8 means about 2 reps left.
- These are estimates for planning training, not medical or coaching advice.

## Writing a program the IronLedger app can import

- Write a CSV with the header `Week,Day,Exercise,Sets,Reps,Load,RPE,RIR,Rest,Notes` and one row per exercise, such as `1,Day 1,Squat,4,5,120,7,,3:00,belt on the last set`. The full format is at https://www.ironledger.app/tools/program-file-checker.
- Write loads as plain numbers in the lifter's unit, or leave Load blank to start from their last load. Text such as "75%" logs its first number when a set is ticked, so put percentages and cues in Notes.
- Wrap any cell that contains a comma in double quotes; never use a double quote inside a cell.
- Before handing the file over, call `check_program_file` with the whole file as `file` (POST JSON for long files) and the planned file name as `fileName`. Fix every `error` issue, and review the `warning`, `match` and `advice` items with the lifter.
- The app names the program after the file. Imported programs keep the loads the file sets: live load recommendations run only on the app's five built-in load-and-go programs.

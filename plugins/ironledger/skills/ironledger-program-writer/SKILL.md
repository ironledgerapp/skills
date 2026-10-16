---
name: ironledger-program-writer
description: Write a strength training program as a file the IronLedger app imports, check it with IronLedger's program file checker, and hand it over ready to import. Use when a lifter wants a program for IronLedger, wants a coach's spreadsheet converted for IronLedger, or wants an existing IronLedger program file changed.
---

# Write a program for IronLedger

IronLedger is a free strength training app (iPhone; Android in closed testing). It imports a program from a CSV file. This skill writes that file correctly the first time and checks it with the same import rules the app uses.

## 1. Ask before writing

Get these from the lifter, or say what you assumed:

- Goal and experience (new to barbells, past novice gains, competing).
- Days a week and how long the block should run, in weeks.
- Equipment, and any lifts to avoid.
- Unit: kg or lb. Loads in the file are read in the unit the app is set to.
- Current numbers for the main lifts, such as recent sets, rep maxes or one-rep maxes, if loads should be filled in.

If they want a well-known program, point them to these first:

- **Built into the app, with live load recommendations:** Starting Strength, Wendler's 5/3/1, PHUL, Push Pull Legs, Upper/Lower Powerbuilding and others (https://www.ironledger.app/programs). They're better than an imported copy, because the app recommends the next load on five of them.
- **Free program files from your numbers:** Texas Method, GZCLP and nSuns 5/3/1 LP (https://www.ironledger.app/programs/texas-method, /programs/gzclp and /programs/nsuns).

## 2. Write the file

One header row, then one row per exercise per session:

```
Week,Day,Exercise,Sets,Reps,Load,RPE,RIR,Rest,Notes
1,Day 1,Squat,4,5,120,7,,3:00,belt on the last set
1,Day 1,Romanian Deadlift,3,8,90,,2,2:00,
1,Day 2,Bench Press,4,5,85,7,,3:00,"pause, then press"
2,Day 1,Squat,4,5,122.5,7.5,,3:00,belt on the last set
```

Rules the app's importer enforces (full reference: https://www.ironledger.app/tools/program-file-checker):

- **Week** is a number (1, 2, 3). **Day** is `Day 1`, `Day 2`… within each week. Without week information, every session lands in week 1.
- **Exercise** is required. Use the exact names in `references/exercise-library.md` wherever one fits. A close miss makes the app ask "Did you mean …?", and an unknown name becomes a new custom exercise with no history.
- **Sets** is a whole number, or a range like `2-3`, which imports as the top number with the range in the notes. If the Sets column is present, a blank cell skips the row.
- **Reps** is text: `5`, `8-12`, `5+` for as many as possible, or one value per set like `"5, 5, 3"`. If the Reps column is present, a blank cell skips the row.
- **Load** is a plain number in the lifter's unit, a range like `100-110`, or one value per set like `"100, 105, 110"`. Leave it blank to start from the lifter's last load. **Never write text such as `75%` or `RPE 8` in Load**: ticking an empty set logs the first number it finds (75 or 8). Put percentages and cues in Notes.
- **RPE** and **RIR** are the effort targets. Leave out both columns if the program has none; with an RIR column, every row without RPE or RIR gets a warning.
- **Rest** is `90`, `90s`, `2 min`, `1:30` or `1m30s`.
- Wrap a cell that contains a comma in double quotes. The app drops every quote character, so never use a double quote inside a cell.
- Supersets and circuits aren't read from a file. Describe them in Notes.

## 3. Check it before handing it over

If you have the IronLedger MCP server (`https://www.ironledger.app/mcp`), call `check_program_file` with:

- `file`: the whole file as text;
- `fileName`: the name it will be saved as, such as `Upper Lower Block.csv`.

Without MCP, POST the same JSON to `https://www.ironledger.app/api/tools/program-file`.

- Fix every issue whose `kind` is `error`; those rows would be skipped.
- Read every `warning` and `match` issue, plus every `advice` item, and fix them or explain them to the lifter.
- Repeat until `imports` is true and nothing unexplained is left.

## 4. Hand it over

- Give the whole file and tell the lifter to save it as `<Program Name>.csv`. **The app names the program after the file.**
- To import it: on the Routine tab with no program loaded, tap Import under Load a program. With a program already loaded, go to the Library, tap +, then Import instead. Choose the file, review the preview, then tap Import.
- Re-importing a file with the same name later offers Update in place, which keeps the weeks already trained, or Import as copy.

## Be honest about what the app does

- An imported program keeps the loads the file sets. The app recommends the next load only on its five built-in load-and-go programs, so don't promise automatic progression for a file.
- A file plans progression as if every session goes to plan. Put the rule for a missed session in Notes for the lifter to apply.
- Credit a named program to its creator, and don't present an altered version as the original.
- This is training guidance, not medical advice.

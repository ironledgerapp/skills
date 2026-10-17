---
name: ironledger-deload-planner
description: Plan a deload week from the published research and coaching guidance on deloading, apply it to the lifter's own program, and write it as rows in an IronLedger program file checked with the app's import rules. Use when a lifter asks for a deload, asks whether they need one, or wants one added to their program.
---

# Plan a deload week

A deload is "a period of reduced training stress designed to mitigate physiological and psychological fatigue, promote recovery, and enhance preparedness for subsequent training". That definition comes from a Delphi panel of expert strength and physique coaches (Bell and colleagues, 2023). This skill picks a deload method from published sources, applies it to the lifter's own program, and writes the week as rows the IronLedger app imports. The quotes behind every rule here are in `references/sources.md`.

## 1. Check whether the program already has one

- **5/3/1:** Jim Wendler's week 4 deload is 40%, 50% and 60% of the training max, for 5 reps each. The training max is 90% of the one-rep max.
- **The IronLedger app's built-in programs:** its built-in 5/3/1 and Challenge to Change already include their deload weeks. Don't add another.
- **Starting Strength** handles a stall with a reset, not a deload week. After a lift is missed twice, its FAQ says to "de-load your weight in that lift by 8-10%" and work back up.
- For any other named program, use the program's own written rule if it has one. Don't invent one in its name.

## 2. Decide whether to deload now

- **Planned:** Bell and colleagues' guidelines (2022) say a pre-planned deload "can be scheduled every 4 to 8 weeks". The coaches they interviewed ranged from 3 to 12 weeks. In a survey of 246 competitive strength and physique athletes, the average was every 5.6 ± 2.3 weeks (Rogerson and colleagues, 2024).
- **Reactive:** athletes in the same survey also deloaded when performance stalled, or during periods of more muscle soreness or joint aches. The `ironledger-training-review` skill can show from an IronLedger export whether a lift has stalled.
- **Not everyone uses them on a schedule:** 65% of the surveyed athletes felt they could progress without deloading.
- **Pain, injury or illness** are for a professional, not a deload.

## 3. Choose the method

There is "no single method of deloading" (Bell and colleagues, 2022), and the sources differ on the details. Give the lifter these sourced options:

- **Length:** "most deloads will last 5 to 7 days" (Bell and colleagues, 2022). The athletes surveyed averaged 6.4 ± 1.7 days.
- **Volume:** reduce it. The Delphi panel agreed universally that volume should come down (Bell and colleagues, 2023). The size of the cut varies by source:
  - Bell and colleagues (2022) suggest about 30–50%, through fewer reps per set, fewer sets per session, or both.
  - Mike Israetel (Juggernaut, 2013) says volume should come down "probably by half or more".
- **Effort or load:** one of the methods in Bell and colleagues (2022):
  - add 1–3 reps in reserve to each set;
  - keep the load and do fewer reps;
  - reduce the load (their example is 10%) and keep the reps.

  Israetel writes that intensity "can actually stay up in the usual range", and that dropping it by 50% for the last half of the week "may be a good start".
- **Training days:** Bell and colleagues' guidelines (2022) say frequency "will typically remain unchanged". In the survey, 63% of athletes kept the same number of weekly sessions and 32.9% cut them.
- **Exercises:** the main exercises can be done with less volume or intensity, and accessories "could be adapted or removed altogether" (Bell and colleagues, 2023).
- **A full week off:** in a trial with resistance-trained adults, stopping resistance training for one week in the middle of a 9-week program led to smaller gains in lower-body strength than training straight through (Coleman and colleagues, 2024). The authors say the result is specific to stopping resistance training; a lighter week wasn't tested.

## 4. Write the deload week

Start from the lifter's normal week: their IronLedger program file if they have it, or the plan they describe. Write the deload as its own week in the same file format the `ironledger-program-writer` skill uses:

```
Week,Day,Exercise,Sets,Reps,Load,RPE,RIR,Rest,Notes
4,Day 1,Squat,2,5,110,,4,3:00,"Deload week: half the sets, 2 more reps in reserve"
4,Day 1,Romanian Deadlift,2,8,80,,4,2:00,"Deload week: half the sets, 2 more reps in reserve"
```

- Keep every exercise name exactly as it is in the normal weeks, so the history stays on the same exercise.
- Write loads as plain numbers in the lifter's unit, rounded to weights they can load. Never write "60%" or "-10%" in Load: the app logs the first number in the cell when a set is ticked. Put the percentage in Notes instead.
- With an RPE or RIR column, lower the RPE target or raise the RIR target to match the method. For example, 2 more reps in reserve takes RIR 2 to RIR 4, or RPE 8 to RPE 6.
- Start each Notes cell with "Deload week" and every change you made, so the lifter can see why the numbers drop. Wrap any cell that contains a comma in double quotes.
- For a 5/3/1 program written as an import file (not the app's built-in 5/3/1), write each lift's three deload sets as one row: Sets `3`, Reps `5`, and one load per set in Load. With a 150 kg training max, that is `"60, 75, 90"`.
- If the deload goes between existing weeks, renumber the weeks after it.

## 5. Check it and hand it over

1. Call `check_program_file` on the IronLedger MCP server (`https://www.ironledger.app/mcp`), with the whole file as `file` and the planned file name as `fileName`. Without MCP, POST the same JSON to `https://www.ironledger.app/api/tools/program-file`.
2. Fix every `error`, and fix or explain every `warning`, `match` and `advice` item. Repeat until `imports` is true and nothing unexplained is left.
3. Give the lifter the whole file. If they already imported the program, save it under the same file name: re-importing it offers Update in place, which keeps the weeks already trained.
4. To label the week in the app after importing: in the Library, tap the program's …, then EDIT, then the week's …, and turn on Deload week. This only labels the week; the loads stay as the file sets them.

## Deload or taper

A taper is for a competition, not for routine recovery. The Delphi panel saw a deload as something that "could occur anywhere in the training programme, while the taper would only occur only before a competition" (Bell and colleagues, 2023). For a powerlifting meet, the taper review by Travis and colleagues (2020) recommends reducing volume by about 30–70%, keeping intensity at or above 85% of the one-rep max or reducing it, over 1–2 weeks, followed by 2–7 days without training. The `ironledger-meet-attempts` skill covers the attempts themselves.

## Be honest

- Name the source of every number you use. Don't add rules of your own.
- An IronLedger import keeps the loads the file sets. The app's load recommendations run only on its five built-in load-and-go programs.
- This is training guidance, not medical advice.

# IronLedger skills

Free Agent Skills for strength training from [IronLedger](https://www.ironledger.app), a free strength training app. Each skill teaches an AI assistant to do one job well. They work with the free IronLedger MCP server at `https://www.ironledger.app/mcp`, which needs no account or key.

| Skill | What it does |
|---|---|
| `ironledger-strength-calculators` | One-rep max, RPE loads, plates per side, warm-up sets, and DOTS, IPF GL and Wilks scores, using IronLedger's calculators |
| `ironledger-program-designer` | Designs a complete training block from the lifter's goal, experience, schedule, equipment and recent sets: evidence-based rules, tested templates (5/3/1 variants, meet prep, hypertrophy, general and injury-aware, rugby, ADF preparation) and every load worked out by script, written as an IronLedger import file and checked |
| `ironledger-program-writer` | Writes a program the lifter already has as a file the IronLedger app imports, then checks it with the app's own import rules before handing it over |
| `ironledger-training-review` | Reviews training from IronLedger's own exports (History CSV or JSON backup): progress on each lift, records, volume and consistency |
| `ironledger-meet-attempts` | Plans opener, second and third attempts for a powerlifting meet from recent training, using the IPF and USAPL rules and published coaching ranges, with plates, warm-ups and DOTS or IPF GL for each plan |
| `ironledger-deload-planner` | Plans a deload week from the published deload research and coaching guidance, and writes it into an IronLedger program file checked with the app's import rules |
| `ironledger-nutrition-plan` | Sets evidence-based calorie and macro targets, builds an Excel meal plan with like-for-like swaps and a weekly check-in sheet (Australian supermarket foods), and reads the check-ins against published adjustment rules |

## Install

**Claude Code.** This adds every skill and connects the IronLedger MCP server:

```
/plugin marketplace add ironledgerapp/skills
/plugin install ironledger@ironledger
```

**Other agents (Codex, Cursor, OpenCode and more):**

```
npx skills add ironledgerapp/skills
```

**Claude.ai (web and desktop).** Download the calculators skill as a zip from https://www.ironledger.app/ai and upload it under Customize, then Skills. That page also has setup steps for connecting the MCP server in Claude, ChatGPT, Gemini, Cursor, VS Code, Codex and others.

## Scripts

The program designer and the nutrition plan come with Python scripts, so every load, calorie and macro number is worked out by code, not by the AI. They need Python 3.9 or later and nothing else, except the nutrition plan's workbook builder, which needs openpyxl (`pip install openpyxl`). Claude.ai's code execution has both.

Tests: `python3 -m unittest discover -s tests -t .` from the repository root. `IRONLEDGER_LIVE=1` also checks every program designer template with the live IronLedger program file checker.

## Safety

The program designer starts with the six questions of the Adult Pre-Exercise Screening System (Stage 1) and writes nothing after a yes until the lifter has a health professional's guidance. Neither the program designer nor the nutrition plan writes anything for anyone under 18. The nutrition plan refuses for pregnancy, breastfeeding, a medical condition, appetite or weight medication, or disordered eating, and points to a doctor or dietitian. None of the skills plans a weigh-in weight cut.

## What these skills can't do

They can't read or change anyone's IronLedger account. The MCP server only calculates and checks the files you send it. The training review works from a file the lifter exports and shares.

## Program files

The program writer follows the IronLedger program file format, documented with a free checker at https://www.ironledger.app/tools/program-file-checker. Ready-made program files for Texas Method, GZCLP and nSuns 5/3/1 LP, built from your own numbers, are at https://www.ironledger.app/programs.

## Sources

The meet attempt and deload skills only use rules and numbers from published sources: federation rulebooks, coaches' own writing and peer-reviewed studies. Each has a `references/sources.md` with the quotes and links. The program designer cites only the PubMed IDs in its `references/evidence.md`, and the nutrition plan only those in its evidence list. Attempt selection and deload timing are judgement calls, and the skills say so.

IronLedger isn't affiliated with the creators of the programs, the coaches or the federations these skills mention. Programs are credited to their creators.

## Licence

MIT. See [LICENSE](LICENSE).

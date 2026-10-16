# IronLedger skills

Free Agent Skills for strength training from [IronLedger](https://www.ironledger.app), a free strength training app. Each skill teaches an AI assistant to do one job well. They work with the free IronLedger MCP server at `https://www.ironledger.app/mcp`, which needs no account or key.

| Skill | What it does |
|---|---|
| `ironledger-strength-calculators` | One-rep max, RPE loads, plates per side, warm-up sets, and DOTS, IPF GL and Wilks scores, using IronLedger's calculators |
| `ironledger-program-writer` | Writes a training program as a file the IronLedger app imports, then checks it with the app's own import rules before handing it over |
| `ironledger-training-review` | Reviews training from IronLedger's own exports (History CSV or JSON backup): progress on each lift, records, volume and consistency |

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

## What these skills can't do

They can't read or change anyone's IronLedger account. The MCP server only calculates and checks the files you send it. The training review works from a file the lifter exports and shares.

## Program files

The program writer follows the IronLedger program file format, documented with a free checker at https://www.ironledger.app/tools/program-file-checker. Ready-made program files for Texas Method, GZCLP and nSuns 5/3/1 LP, built from your own numbers, are at https://www.ironledger.app/programs.

IronLedger isn't affiliated with the creators of the programs these skills mention. Programs are credited to their creators.

## Licence

MIT. See [LICENSE](LICENSE).

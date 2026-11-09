# Joto Mjini

**Mapping urban heat and cooling inequality across Nairobi.**

A data story about urban heat in Nairobi: which parts of the city get hottest on hot days, who lives there, and how trees, open ground and roofs relate to that heat. It ends with an interactive map where anyone can find their ward and compare it with the rest of the city. Built for the Earthna and CIFF workshop "Land, Food and Heat Resilience in Africa's Arid Regions", Nairobi, 26 November 2026.

"Joto Mjini" is the working name (Swahili for "heat in the city"). Other names considered: Nairobi's Heat Divide (kept as the story's headline frame), Nairobi Heat Atlas, Joto Atlas, Joto Map, Nairobi Joto Lab. To rename, search the project for "Joto Mjini" and replace it.

This is a separate project from the El Niño urban overlay. The El Niño project can later reuse this pipeline's boundary, buildings and basemap and add rainfall.

## How the work is split

- **Opus 5.5 in Claude Code (Faniki account)** does the build, following the prompts in `prompts/`.
- **Claude in the Claude app** reviews what Opus produces.
- **Stephane** decides, does the final human QA, and presents.
- **Tony Widjarnaso** reviews the urban analysis if he has capacity.

## Tonight's overnight run

1. **Plug in your charger.** In Terminal, run `caffeinate -dims` and leave that window open, so the Mac does not sleep. Press Control-C in that window in the morning to stop it.
2. **Open this folder in VS Code** (File, Open Folder, `~/Desktop/joto-mjini`).
3. **Optional:** copy `.env.example` to `.env` and add your Copernicus Data Space credentials if you have them. The run works without them.
4. **Open Claude Code** in VS Code, sign in with your Faniki account and choose Opus 5.5.
5. **Install the permissions file.** Run this once in Terminal (the remote tools are not allowed to write into a `.claude` folder, so the file waits in `setup/`):

   ```
   mkdir -p ~/Desktop/joto-mjini/.claude && mv ~/Desktop/joto-mjini/setup/claude-settings.json ~/Desktop/joto-mjini/.claude/settings.json
   ```

   The file `.claude/settings.json` lets Opus run the data, Python and site commands without stopping to ask, and blocks `git push`, deleting files, `sudo` and reading `.env`. A few commands may still ask for approval; if the run stalls on one in the morning, approve it and tell Opus to continue.
6. **Paste this as your first message:**

   > Read prompts/00_START_HERE_tonight.md and follow it exactly, through all four phases, without stopping to ask me anything.

7. **In the morning,** open `MORNING_REPORT.md` first, then `analysis/FINDINGS.md`, then run the site with `cd site && npm run dev`. Bring the report back to Claude for review.

## Files

| File | What it is |
|---|---|
| `CLAUDE.md` | Rules Opus reads every session: data honesty, ethics, writing style, never stop, never push |
| `DESIGN_RULES.md` | Stephane's no-vibe-coding rules, mandatory for the site |
| `prompts/00_START_HERE_tonight.md` | The overnight run, phase by phase |
| `prompts/01_data_pipeline.md` | Datasets, sources, fallbacks, processing |
| `prompts/02_analysis.md` | The questions, outputs and checks |
| `prompts/03_story_site.md` | The story site, modelled on NASA's LA fires story |
| `prompts/04_qa_and_report.md` | QA, screenshots, presentation outline, morning report |
| `reference/la-fires.stories.mdx` | Source of NASA's "Fanning the Flames" story |
| `reference/README.md` | How the NASA story is built, and African equivalents of NLCD and NLDAS |
| `reference/workshop_brief.md` | The workshop details |
| `docs/application_draft.md` | Draft answers for the workshop application form |

## Timeline to 26 November

- [ ] Tonight, 10 November: overnight run 1 (data, analysis, first site)
- [ ] 11 November: review the morning report with Claude; submit the workshop application (rolling review, closes 20 November)
- [ ] 11 to 14 November: run 2 to fix problems and polish the writing
- [ ] 15 to 17 November: send to Tony for review
- [ ] 18 to 21 November: revisions; publish to GitHub Pages
- [ ] 22 to 25 November: slides and rehearsal, with offline screenshots as a backup
- [ ] 26 November: workshop

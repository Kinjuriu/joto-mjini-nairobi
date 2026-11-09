# Prompt 00: tonight's overnight run (paste this into Claude Code)

You are working overnight, unattended, on Stephane's laptop. She is asleep and will read your results in the morning. Nobody can answer questions until then, so follow `CLAUDE.md` exactly: never stop to ask, log questions and decisions, fail soft, commit locally after each milestone, never push, never delete.

## Your job tonight

Take the project from an empty folder to:

1. a working, reproducible Python data pipeline for Nairobi surface temperature and its context layers;
2. a first analysis with real numbers, each one traceable;
3. a working first version of the story website, modelled on NASA's "Fanning the Flames" story, running locally;
4. a QA pass with screenshots and a clear morning report.

Quality and honesty matter more than finishing everything. A smaller story with real, checked numbers is a success. A complete-looking story with any invented number is a failure.

## Before you start (about 20 minutes)

1. Read, in this order: `CLAUDE.md`, `DESIGN_RULES.md`, `reference/README.md`, `reference/workshop_brief.md`, then skim `reference/la-fires.stories.mdx` end to end so you understand how the NASA story is built.
2. Read `prompts/01_data_pipeline.md`, `prompts/02_analysis.md`, `prompts/03_story_site.md` and `prompts/04_qa_and_report.md` in full before writing any code, so early choices support later steps.
3. If `PROGRESS.md` already exists, this is a resumed run: read `PROGRESS.md`, `DECISIONS.md` and `QUESTIONS.md`, then continue from the first unfinished step. Do not redo finished work.
4. Otherwise: run `git init` (only if there is no `.git`), create `PROGRESS.md`, `DECISIONS.md` and `QUESTIONS.md`, set up `uv` and the `.venv`, and make the first commit "Project skeleton".
5. Note the start time in `PROGRESS.md`.

## The phases

Work through these in order. Each has its own detailed prompt. The time budgets are a guide; if a phase runs well over, cut scope inside that phase (the prompts say what is optional) and move on, so every phase gets done.

| Phase | Prompt | Budget | Must produce |
|---|---|---|---|
| 1. Data pipeline | `prompts/01_data_pipeline.md` | about 3.5 hours | Nairobi boundary and wards, Landsat surface temperature scenes and composites, context layers, `data/SOURCES.md` |
| 2. Analysis | `prompts/02_analysis.md` | about 2 hours | ward statistics, building values, charts data, `analysis/FINDINGS.md` |
| 3. Story site | `prompts/03_story_site.md` | about 3 hours | the site in `site/`, building and running locally, with real data |
| 4. QA and report | `prompts/04_qa_and_report.md` | about 1 hour | screenshots, checklist, `MORNING_REPORT.md`, presentation outline |

At the end of each phase: update `PROGRESS.md`, commit with the message "Phase N: [what was done]", and only then start the next phase.

## If something goes badly wrong

- No network or a core source is down: switch to the fallback source in prompt 01. If every Landsat source fails, stop the data phase, build the site with clearly marked placeholders, and explain exactly what failed in `MORNING_REPORT.md`, including the error messages and the commands Stephane can run to retry.
- Disk space: keep raw downloads clipped to the Nairobi area as you go. If free space falls under 10 GB, stop downloading, record it, and work with what you have.
- A Python or npm install fails: try once more, then try the alternative package named in the prompt, then record it and work around it.

## Stop condition

You are done when `MORNING_REPORT.md` exists, is complete as described in prompt 04, and the final commit is made. Do not start new features after that. If time remains, use it only for the "if time remains" lists in the prompts, in the order given.

Begin now with "Before you start".

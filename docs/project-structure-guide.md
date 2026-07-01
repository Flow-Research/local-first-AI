# Local-First AI Context Assistant: Project Structure Guide

## Purpose Of This Guide

This guide explains how the repository is organized and why the structure supports learning, research, design, building, verification, and fellowship collaboration.

The baseline is not designed so AI can do everything. It is designed so people can learn while using AI responsibly as a helper.

## Core Philosophy

The project follows one simple rule:

```text
One week = one concept + one small output + one report.
```

Every week should produce evidence that a contributor learned something, made a design choice, built or inspected something, and verified the result.

## Why The Structure Creates Learning

The folder structure forces each contribution to pass through a learning loop:

```text
Research
  |
Design
  |
Build
  |
Verify
  |
Document
  |
Review
  |
Merge to master
```

This means contributors are not only adding code. They are also building understanding.

## The Role Of `master`

`master` is the clean baseline. It should always be stable enough for a new fellow to branch from.

All work should happen on a branch:

```text
master
  |
feature/month-02-week-01-context-prep
research/month-05-crdt-sync
design/month-03-demo-flow
docs/fellowship-guide
experiment/month-08-network-exchange
fix/readme-links
```

The branch returns to `master` only after learning, design, build output, and verification evidence are documented.

## Main Repository Areas

| Area | Purpose |
|---|---|
| `README.md` | Short project front page |
| `PROJECT_BRIEF.md` | Stable project purpose and scope |
| `CONTRIBUTING.md` | Fellowship rules for contribution |
| `docs/` | Durable documentation and process guides |
| `docs/roadmap.md` | Full 12-month learning, design, and build roadmap |
| `reports/` | Weekly public learning journal |
| `research/` | Paper notes, reading lists, and learning logs |
| `design/` | Design outcomes, sketches, and decisions |
| `features/` | Feature briefs and feature lifecycle notes |
| `src/` | Code implementation |
| `benchmarks/` | Measurement scripts, results, and reports |
| `assets/` | Screenshots, diagrams, and evidence |
| `tests/` | Automated checks |
| `.github/` | Pull request checklist |
| `scripts/` | Local verification scripts |

## Reports Folder

The `reports/` folder contains `month-01` through `month-12`.

Each month has four weekly report files. Every fellow adds a short named block to the relevant shared report.

Weekly reports should include:

- Goal for the week.
- Research / learning.
- Design outcome.
- What was built.
- Files added or changed.
- Evidence.
- Problems or blockers.
- Next step.

## Research Folder

The `research/` folder keeps learning visible.

| Folder | Purpose |
|---|---|
| `research/paper-notes/` | Notes from papers and technical sources |
| `research/reading-lists/` | Monthly or topic-based reading lists |
| `research/learning-logs/` | Human reflection on what was learned |

Research notes should not only summarize a paper. They should explain what the paper means for the project.

## Design Folder

The `design/` folder turns research into decisions.

Design outcomes should answer:

- What problem are we solving?
- What options were considered?
- What did we choose?
- Why did we choose it?
- What evidence supports it?
- What risk remains?

This keeps design work visible and reviewable.

## Features Folder

The `features/` folder prevents feature work from becoming random.

| Folder | Purpose |
|---|---|
| `features/proposals/` | Ideas not started yet |
| `features/active/` | Feature briefs for work in progress |
| `features/completed/` | Finished feature summaries |

Before coding a meaningful feature, contributors should write a feature brief.

## Human Work And AI Assistance

AI may help with explanation, drafting, code suggestions, and review.

Humans remain responsible for:

- Reading and understanding.
- Deciding what matters.
- Reviewing AI output.
- Running checks.
- Explaining design choices.
- Recording evidence.

The fellowship should avoid commits where AI-generated content appears without human understanding or review.

## Verification Model

Verification has two layers.

### Script Verification

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-contribution.ps1
```

The script checks:

- Required docs exist.
- All 12 report months exist.
- Each month has 4 weekly reports.
- Reports contain research, design, and evidence sections.
- Contribution and pull request docs exist.

### Human Verification

A reviewer should ask:

- Can the contributor explain the work?
- Is there evidence of learning?
- Is the design choice documented?
- Is AI assistance disclosed or reviewed?
- Does the weekly report show what changed?
- Can another fellow continue from this commit?

## Pull Request Review

The pull request template requires:

- Branch from the matching `weeks/month-XX-week-YY` branch.
- Weekly report update.
- Verification evidence.
- AI-use review.

This makes every merge teachable and reviewable.

## How A Fellow Should Work Each Week

1. Start from the matching weekly branch.
2. Create a focused fellow branch.
3. Read the weekly paper or technical source.
4. Build the smallest useful output.
5. Verify it with a test, benchmark, screenshot, command output, or manual review.
6. Add your name, topic, at least 20 words about what you did, and public-output link to the weekly report.
7. Run the verification script.
8. Open a pull request to the matching weekly branch.
9. Review with another person.
10. Merge only when the work is understandable.

The weekly report is the only documentation file fellows must update. Extra research, design, feature, or learning documents are optional unless the task explicitly requires them.

## What Good Progress Looks Like

Good progress is not only code volume.

Good progress looks like:

- A small working artifact.
- A clear explanation.
- A learning note.
- A design decision.
- Verification evidence.
- Honest blockers.
- A next step.

## Why This Baseline Matters

The baseline gives the fellowship a shared way to work.

It protects `master`, keeps learning visible, makes AI use accountable, and gives new contributors a clear path into the project.

The structure is intentionally simple. It should help the project grow for 12 months without needing major reorganization.

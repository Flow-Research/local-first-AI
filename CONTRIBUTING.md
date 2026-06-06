# Contributing Guide

This project is a fellowship-style learning project. The goal is not for AI to do all the work. The goal is for contributors to learn, design, build, verify, and document the work with AI as a helper.

## Core Rule

`master` is the clean baseline. Do not work directly on `master`.

Every meaningful contribution should happen on a branch created from `master`.

## Branch Naming

| Work Type | Branch Pattern | Example |
|---|---|---|
| Feature | `feature/month-XX-week-YY-short-name` | `feature/month-02-week-01-context-prep` |
| Research | `research/month-XX-topic` | `research/month-05-crdt-sync` |
| Design | `design/month-XX-topic` | `design/month-03-demo-flow` |
| Experiment | `experiment/month-XX-topic` | `experiment/month-08-network-exchange` |
| Documentation | `docs/topic` | `docs/fellowship-guide` |
| Fix | `fix/topic` | `fix/readme-links` |

## Required Learning Evidence

Every weekly branch should include:

- A weekly report in `reports/month-XX/`.
- A human learning log in `research/learning-logs/` when the work involved learning.
- A paper note in `research/paper-notes/` when a paper or technical source influenced the work.
- A design outcome in `design/outcomes/` when a design, architecture, flow, or data model changed.
- A feature brief in `features/active/` or `features/completed/` when a feature was planned or finished.
- Evidence of verification in the weekly report, benchmark output, screenshots, tests, or command output.

## Human Work And AI Assistance

AI may help with:

- Explaining papers.
- Drafting templates.
- Suggesting code.
- Reviewing structure.
- Generating first drafts.

Humans must still:

- Read and summarize the important ideas.
- Decide what to build.
- Explain design choices.
- Run or inspect verification evidence.
- Write reflection notes.
- Review AI output before commit.

## Before Opening A Pull Request

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-contribution.ps1
```

Then fill the pull request checklist in `.github/PULL_REQUEST_TEMPLATE.md`.

## Merge Standard

A branch should only merge back to `master` when another person can understand:

- What was learned.
- What was designed.
- What was built.
- What was verified.
- What still needs work.

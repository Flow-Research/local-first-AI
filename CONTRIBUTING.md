# Contributing Guide

This project is a fellowship-style learning project. The goal is not for AI to do all the work. The goal is for contributors to learn, design, build, verify, and document the work with AI as a helper.

## Core Rule

`master` is the evolving stable project branch. Do not work directly on `master`.

Every meaningful contribution should happen on a branch created from `master`.

New fellows who are starting at Week 1 should branch from `baseline/week-01-starter` instead of the current `master`.

The tag `v0.1-week-01-baseline` marks the immutable Week 1 starter snapshot.

## Branch Naming

| Work Type | Branch Pattern | Example |
|---|---|---|
| Feature | `feature/month-XX-week-YY-short-name` | `feature/month-02-week-01-context-prep` |
| Research | `research/month-XX-topic` | `research/month-05-crdt-sync` |
| Design | `design/month-XX-topic` | `design/month-03-demo-flow` |
| Experiment | `experiment/month-XX-topic` | `experiment/month-08-network-exchange` |
| Documentation | `docs/topic` | `docs/fellowship-guide` |
| Fix | `fix/topic` | `fix/readme-links` |
| Fellow Work | `fellows/<github-username>/month-XX-week-YY-<topic>` | `fellows/ada/month-03-week-02-sync-test` |

## New Fellow Start

```bash
git checkout baseline/week-01-starter
git checkout -b fellows/<github-username>/month-01-week-01-setup
```

## Required Learning Evidence

Every weekly branch should include:

- A short named block in the existing `reports/month-XX/week-YY.md` report.
- A human learning log in `research/learning-logs/` when the work involved learning.
- A paper note in `research/paper-notes/` when a paper or technical source influenced the work.
- A design outcome in `design/outcomes/` when a design, architecture, flow, or data model changed.
- A feature brief in `features/active/` or `features/completed/` when a feature was planned or finished.
- A link to the fellow's public post in the weekly report.
- Evidence of verification in benchmark output, screenshots, tests, command output, or the pull request.

Each fellow edits only their numbered block, such as `Fellow 1: Ada`. The block contains the fellow's topic, what they did, and their public-output link. See `reports/README.md` for the format.

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

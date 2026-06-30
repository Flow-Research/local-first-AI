# Documentation Guide

## What Goes Where

| Document Area | Use It For |
|---|---|
| `README.md` | Short public overview and links to major docs |
| `docs/roadmap.md` | Full 12-month roadmap and weekly plan |
| `CONTRIBUTING.md` | Fellowship contribution rules and branch expectations |
| `docs/baseline-start-guide.md` | How new fellows start from the Week 1 baseline |
| `docs/releases/` | Release notes for baseline and future milestone snapshots |
| `PROJECT_BRIEF.md` | Stable reason for the project |
| `docs/architecture.md` | Current system architecture |
| `docs/decisions.md` | Durable decisions and reasons |
| `docs/fellowship-learning-model.md` | How contributors learn while building |
| `docs/commit-verification.md` | What must be verified before merge |
| `docs/branching-and-features.md` | Branch and feature workflow |
| `docs/research-and-design-architecture.md` | Research, design, build, and documentation loop |
| `reports/` | One shared report per week with a short block for each fellow |
| `research/paper-notes/` | Notes from papers and technical sources |
| `research/learning-logs/` | Human learning reflections |
| `design/outcomes/` | Design decisions, sketches, and outcomes |
| `src/python/`, `src/c/`, `src/cpp/`, `src/rust/` | Language-specific implementation areas |
| `tests/python/`, `tests/c/`, `tests/cpp/`, `tests/rust/` | Language-specific tests and verification |

## Keep README Clean

The README should answer:

- What is this project?
- What phase is it in?
- Where is the roadmap?
- Where are the reports?
- How is the repo organized?

Detailed plans belong in `docs/`.

## Learning Documentation Rule

Every meaningful branch should leave behind evidence of human learning. This can be a weekly report, paper note, learning log, design outcome, benchmark result, screenshot, or review note.

The question is not only "Did the code change?" The better question is:

> Can another fellow understand what was learned, what was decided, what was built, and what was verified?

## Fellow Weekly Update

Each week uses one existing report:

```text
reports/month-XX/week-YY.md
```

Each contributor fills in a numbered block such as `Fellow 1: Full Name`. Keep it short: add only the topic, what the fellow did, and a link to their public output.

Only edit your own fellow block. Git records the contribution through the commit on your branch.

## Multi-Language Documentation Rule

Keep the weekly report short even when work introduces Python, C, C++, or Rust. Put details such as the following in the relevant feature brief, design outcome, test, or learning log:

- Why that language was chosen for the task.
- How the code was run or checked.
- What tradeoff the language introduced.
- Whether the code is prototype, experiment, or stable baseline.

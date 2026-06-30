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
| `reports/` | Project week overviews and short, independently mergeable fellow updates |
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

Each fellow creates their own file:

```text
reports/month-XX/week-YY-fellow-<github-username>.md
```

Copy `docs/templates/weekly-report-template.md` and keep the update short. It only needs the fellow's name, topic, what they did, commit or pull request links, a public-post link, and one blocker or next step.

Do not combine several fellows in one editable file. The files with the same `month-XX` and `week-YY` form that week's report, while keeping each person's branch and commits easy to review.

## Multi-Language Documentation Rule

When work introduces Python, C, C++, or Rust code, the weekly report should say:

- Why that language was chosen for the task.
- How the code was run or checked.
- What tradeoff the language introduced.
- Whether the code is prototype, experiment, or stable baseline.

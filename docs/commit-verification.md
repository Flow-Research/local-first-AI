# Commit Verification

The project uses verification to make sure commits show real learning, design, and work.

## What Verification Means

Verification does not mean the project is perfect. It means each contribution leaves enough evidence for another person to understand and review it.

## Required Evidence By Work Type

| Work Type | Required Evidence |
|---|---|
| Research | Paper note, source link, human summary, project implication |
| Design | Design outcome, options considered, chosen direction, risk |
| Feature | Feature brief, code change, verification evidence, weekly report |
| Benchmark | Runner or method, result file, interpretation note |
| Documentation | Updated doc, reason for change, reviewer-readable explanation |
| Experiment | Hypothesis, method, result, decision on whether to continue |
| Python code | Run output, test, benchmark, or CLI evidence |
| C code | Build output, run output, and safety notes where relevant |
| C++ code | Build output, run output, benchmark, and interface notes |
| Rust code | `cargo check`, `cargo test`, run output, or safety/design note |

## Baseline Verification Script

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-contribution.ps1
```

The script checks that:

- Core docs exist.
- All 12 report months exist.
- Each report month has 4 project week overviews and may also contain one independently mergeable update per fellow per week.
- Weekly reports include research, design, and evidence sections.
- Contribution and pull request documents exist.

## Human Review

The script is not enough by itself. A reviewer should also check:

- Does the contributor explain the work in their own words?
- Is AI use reviewed and disclosed?
- Does the design outcome connect to research or evidence?
- Does the report show what was difficult or uncertain?
- Can another person continue from this commit?

## Baseline Review

`baseline/week-01-starter` is intended to remain stable. It should not receive normal weekly work.

New work belongs on:

- `fellows/<github-username>/month-XX-week-YY-<topic>`
- `feature/month-XX-week-YY-topic`
- `research/month-XX-topic`
- `design/month-XX-topic`
- `docs/topic`
- `fix/topic`

## Good Commit Shape

A good weekly commit usually touches several areas:

```text
reports/month-XX/week-YY-fellow-<github-username>.md
research/paper-notes/...
design/outcomes/...
features/active or features/completed/...
src/...
tests/ or benchmarks/ or assets/
```

Not every branch touches every folder, but every branch should be understandable.

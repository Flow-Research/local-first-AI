# Architecture

## Project Working Architecture

This repository is organized around a research-to-design-to-build loop.

```text
master branch
  |
new branch
  |
Research input
  |
Design outcome
  |
Feature brief
  |
Code / benchmark / docs change
  |
Weekly report
  |
merge back to master
```

`master` should stay clean. It is the stable baseline used to start each feature, research, design, documentation, experiment, or fix branch.

## Repository Architecture

```text
research/        paper notes and reading lists
  |
design/          outcomes, sketches, flows, diagrams
  |
features/        scoped feature briefs
  |
src/             implementation
  |
benchmarks/      measurement
  |
assets/          screenshots, diagrams, evidence
  |
reports/         weekly public learning journal
  |
docs/            durable architecture, roadmap, decisions, process docs
```

## Language Architecture

The implementation stack is intentionally multi-language:

| Language | Primary Role | Folder |
|---|---|---|
| Python | Fast prototypes, CLI flows, orchestration, AI/context experiments, benchmark scripts | `src/python/` |
| C | Low-level systems experiments, device-facing code, storage/runtime fundamentals | `src/c/` |
| C++ | Performance-oriented local runtime experiments and systems prototypes | `src/cpp/` |
| Rust | Safety-focused systems modules, tooling, and future reliable local components | `src/rust/` |

Shared ideas should be written language-neutrally first in `src/shared/`, `docs/`, `design/outcomes/`, or `features/`. Code should move into a language folder only when the week has a clear build reason.

## Multi-Language Verification

| Work Type | Expected Verification |
|---|---|
| Python | Script run, unit test, CLI transcript, benchmark, or report evidence |
| C | Build command, compiler warnings review, run output, memory/safety notes where relevant |
| C++ | Build command, run output, benchmark, and interface notes |
| Rust | `cargo check`, `cargo test`, run output, or safety/design note |
| Cross-language design | Interface contract, schema, data-flow diagram, and design outcome |

## Month 1 System Architecture

```text
User
  |
Command Line Interface
  |
Application Logic
  |
SQLite Local Database
  |
Local Notes / Context
```

## Intended System Growth

```text
User
  |
CLI or App Interface
  |
Local App Logic
  |
SQLite Database
  |
Context Retrieval
  |
Local AI Model
```

## Current Principle

Start with the local-first base layer before adding advanced AI. The first question is whether the system can store, retrieve, update, and preserve local user-owned data reliably.

## Documentation Architecture

| Artifact | Where It Lives | When To Update |
|---|---|---|
| Project purpose | `PROJECT_BRIEF.md` | When scope or motivation changes |
| Full roadmap | `docs/roadmap.md` | When the 12-month plan changes |
| Branching workflow | `docs/branching-and-features.md` | When the development process changes |
| Research notes | `research/paper-notes/` | When a paper informs the work |
| Design outcomes | `design/outcomes/` | When a design choice is made |
| Feature briefs | `features/active/` | Before implementing a scoped feature |
| Weekly reports | `reports/month-XX/` | Every week |
| Benchmarks | `benchmarks/results/` and `benchmarks/reports/` | When measuring behavior |

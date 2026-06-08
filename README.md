# Local-First AI Context Assistant

A progressive project exploring local-first AI computing, offline-first data, local AI workflows, benchmarking, and device-agent experiments.

The repository is both the project workspace and the learning journal. Each week should produce one small technical output and one short written report.

## Project Status

Current phase: Month 1 - Setup and Base Layer

## Main Goal

Build a simple local-first AI system that can work with local data before adding sync, benchmarking, and device-agent experiments.

## Project Framing Diagram

![Local-First AI Project Framing](assets/images/Local_First%20_AI.png)

## Key Documents

| Document | Purpose |
|---|---|
| [Project Brief](PROJECT_BRIEF.md) | Stable project purpose, scope, and limits |
| [Contributing Guide](CONTRIBUTING.md) | Fellowship rules for branching, learning evidence, and human review |
| [Roadmap](docs/roadmap.md) | Full 12-month plan with weekly build, design, and learning outcomes |
| [Fellowship Learning Model](docs/fellowship-learning-model.md) | How contributors learn while building with AI as a helper |
| [Commit Verification](docs/commit-verification.md) | How commits are checked for learning, design, evidence, and review |
| [Branching and Features](docs/branching-and-features.md) | How to branch from `master` and organize feature work |
| [Research and Design Architecture](docs/research-and-design-architecture.md) | How research, design, build, evaluation, and documentation connect |
| [Documentation Guide](docs/documentation-guide.md) | What belongs in README, docs, reports, research, and design folders |
| [Architecture](docs/architecture.md) | Current system architecture |
| [Decisions](docs/decisions.md) | Durable decisions and reasons |

## Repository Flow

Plan -> Learn -> Build -> Test -> Report -> Commit -> Publish

Use one simple rule: one week = one concept + one small output + one report.

All active work branches from `master`. `master` stays clean and serves as the baseline for new feature, research, design, docs, experiment, and fix branches.

Before a branch is merged, contributors should run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-contribution.ps1
```

The verification script checks the baseline structure, but human review is still required. Contributors must be able to explain what they learned, what they designed, what they built, and how they verified it.

## Folder Intention

| Folder/File | Purpose |
|---|---|
| `PROJECT_BRIEF.md` | Why the project exists and what is in scope |
| `docs/roadmap.md` | The progressive 12-month roadmap |
| `docs/` | Architecture notes, benchmarking notes, compute targets, and decisions |
| `reports/` | Weekly learning and build journal |
| `reports/month-01` to `reports/month-12` | Monthly report folders with four weekly reports each |
| `research/` | Paper notes, reading lists, and learning evidence |
| `research/learning-logs/` | Human learning reflections and AI-use notes |
| `design/` | Design outcomes, sketches, flows, and decision artifacts |
| `features/` | Feature briefs, active feature scope, and completed feature summaries |
| `.github/PULL_REQUEST_TEMPLATE.md` | Pull request checklist for human learning, AI review, and verification |
| `scripts/verify-contribution.ps1` | Local verification script for structure and report requirements |
| `src/` | Actual application code organized by language and domain |
| `src/python/` | Python prototypes, orchestration, CLI work, AI/context experiments |
| `src/c/` | C systems code, low-level storage or device-facing experiments |
| `src/cpp/` | C++ performance, local runtime, and systems experiments |
| `src/rust/` | Rust safety-focused systems modules and future tooling |
| `src/shared/` | Shared schemas, notes, interfaces, and language-neutral design assets |
| `src/storage/` | Cross-language storage design notes or shared storage modules |
| `src/ai/` | Cross-language AI and context-building design notes or shared modules |
| `src/sync/` | Future sync experiments |
| `src/agents/` | Future task-oriented assistant flows |
| `src/network/` | Future trusted local network experiments |
| `src/evaluation/` | Future evaluation helpers |
| `data/` | Local development data, kept out of Git when needed |
| `benchmarks/` | Performance checks and measurement scripts |
| `benchmarks/python`, `benchmarks/c`, `benchmarks/cpp`, `benchmarks/rust` | Language-specific benchmark work |
| `assets/` | Screenshots, diagrams, and report evidence |
| `tests/` | Automated quality checks organized by language |

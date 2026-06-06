# Research And Design Architecture

This project is not only a coding project. It is a research, design, build, and documentation project.

## Working Loop

```text
Research
  |
Design
  |
Build
  |
Evaluate
  |
Document
  |
Merge to master
```

## Repository Areas

| Area | Purpose | Output |
|---|---|---|
| `research/` | Read papers and capture technical lessons | Paper notes, reading lists, research questions |
| `design/` | Turn research into system choices | Diagrams, design outcomes, interface flows |
| `features/` | Scope features before coding | Feature briefs and completion notes |
| `src/` | Build the actual system | Python modules and experiments |
| `benchmarks/` | Measure behavior | Results and benchmark reports |
| `assets/` | Store visual evidence | Diagrams, screenshots, images |
| `reports/` | Publish weekly progress | Weekly reports for every month |
| `docs/` | Explain durable decisions | Roadmap, architecture, decisions, process docs |

## Research Note Pattern

Each paper note should answer:

- What problem does this paper address?
- What idea matters for this project?
- What design question does it raise?
- What should be tested or built because of it?

## Design Outcome Pattern

Each design outcome should include:

- Problem or question
- Design option chosen
- Alternatives considered
- Reason for the choice
- Evidence or research source
- Next design risk

## Documentation Rule

Documentation should be created close to the work. If a branch changes the system, it should also update the matching explanation.

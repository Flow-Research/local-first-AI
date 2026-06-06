# Source Layout

Implementation is organized by language and supported by shared design notes.

| Folder | Purpose |
|---|---|
| `python/` | Fast prototypes, CLI flows, orchestration, AI/context experiments |
| `c/` | Low-level systems and device-facing experiments |
| `cpp/` | Performance-oriented systems prototypes |
| `rust/` | Safety-focused systems modules and tooling |
| `shared/` | Language-neutral schemas, contracts, and interface notes |
| `storage/` | Shared storage design or cross-language storage modules |
| `ai/` | Shared AI/context design or cross-language modules |
| `agents/` | Task-oriented assistant flows |
| `sync/` | Sync experiments |
| `network/` | Local network experiments |
| `evaluation/` | Evaluation helpers |

Before adding code, explain the language choice in the weekly report or feature brief.

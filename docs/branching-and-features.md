# Branching And Feature Organization

## Branching Rule

`master` is the evolving stable project branch. Do not do active work directly on `master`.

Every project task should branch from `master`, stay small, and return to `master` only when the work is documented, reviewed, and safe to build on.

The clean Week 1 starter baseline lives at `baseline/week-01-starter` and is also marked by the `v0.1-week-01-baseline` tag.

New fellows who start from Week 1 should branch from `baseline/week-01-starter`, not from whatever `master` has become later in the fellowship.

## Branch Types

| Branch Type | Use For | Example |
|---|---|---|
| `feature/` | Product or code functionality | `feature/month-02-week-01-context-prep` |
| `research/` | Paper reading, experiments, and notes | `research/month-05-crdt-sync` |
| `design/` | Architecture, flows, diagrams, and prototypes | `design/month-03-demo-storyboard` |
| `experiment/` | Temporary technical trials | `experiment/month-08-network-exchange` |
| `fix/` | Small corrections | `fix/readme-links` |
| `fellows/` | Individual fellow learning branches | `fellows/ada/month-03-week-02-sync-test` |
| `docs/` | Documentation-only work | `docs/month-01-report-cleanup` |

## Feature Folder Flow

Use `features/` to keep feature thinking separate from final code.

| Folder | Purpose |
|---|---|
| `features/proposals/` | Ideas not started yet |
| `features/active/` | Current feature briefs |
| `features/completed/` | Finished feature briefs and summaries |

## Recommended Feature Lifecycle

1. Branch from `master`.
2. Create a feature brief in `features/active/`.
3. Add research notes in `research/paper-notes/` if the work depends on a paper or technical source.
4. Add design outcomes in `design/outcomes/`.
5. Implement the smallest useful code change in `src/`.
6. Add tests, benchmark evidence, screenshots, or command output.
7. Fill in your named fellow block in the existing weekly report.
8. Merge back to `master` only when the branch is coherent and documented.

## Merge Checklist

| Check | Required? |
|---|---|
| Branch started from latest `master` | Yes |
| Weekly report updated | Yes |
| Human learning log added when learning happened | Yes |
| Design outcome added when UI, flow, architecture, or data model changed | Yes |
| Research note added when a paper influenced the work | Yes |
| Tests or manual verification recorded | Yes |
| README changed only when the public project overview changed | Yes |

Before requesting a merge, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-contribution.ps1
```

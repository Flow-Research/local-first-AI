# Branching And Feature Organization

## Branching Rule

`master` is the evolving stable project branch. Do not do active work directly on `master`.

Create one integration branch for the active week from `master`. Each fellow branches from that weekly branch, stays small, and merges back into the same weekly branch after review.

```text
fellows/<github-username>/month-XX-week-YY-<topic>
        -> weeks/month-XX-week-YY
        -> master
```

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
| `weeks/` | Reviewed weekly integration branches | `weeks/month-03-week-02` |
| `docs/` | Documentation-only work | `docs/month-01-report-cleanup` |

## Feature Folder Flow

Use `features/` to keep feature thinking separate from final code.

| Folder | Purpose |
|---|---|
| `features/proposals/` | Ideas not started yet |
| `features/active/` | Current feature briefs |
| `features/completed/` | Finished feature briefs and summaries |

## Recommended Feature Lifecycle

1. Branch from the matching `weeks/month-XX-week-YY` branch.
2. Create a feature brief in `features/active/`.
3. Add research notes in `research/paper-notes/` if the work depends on a paper or technical source.
4. Add design outcomes in `design/outcomes/`.
5. Implement the smallest useful code change in `src/`.
6. Add tests, benchmark evidence, screenshots, or command output.
7. Fill in your named fellow block in the existing weekly report.
8. Open a pull request into the matching weekly branch.
9. Merge the weekly branch into `master` after all fellow contributions are reviewed together.

## Merge Checklist

| Check | Required? |
|---|---|
| Fellow branch started from the matching weekly branch | Yes |
| Pull request targets the matching weekly branch | Yes |
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

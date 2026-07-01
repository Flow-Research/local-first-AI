# Baseline Start Guide

This project keeps `master` as the evolving stable project, while `baseline/week-01-starter` stays as the clean Week 1 starter point for new fellows.

## Branch And Tag Roles

| Name | Type | Purpose |
|---|---|---|
| `master` | Branch | Evolving stable project branch |
| `weeks/month-XX-week-YY` | Branch | Combines reviewed fellow contributions for one week |
| `baseline/week-01-starter` | Branch | Permanent Week 1 starter baseline |
| `v0.1-week-01-baseline` | Tag / release | Immutable snapshot of the Week 1 starter baseline |

## Why This Exists

Fellows may join at different times. If the main group is already at Week 10, a new fellow still needs a clean Week 1 starting point.

The baseline branch and tag solve that:

- `master` keeps moving as the shared project matures.
- `baseline/week-01-starter` remains the branch new fellows can start from.
- `v0.1-week-01-baseline` marks the exact starter snapshot forever.

Release notes live in [docs/releases/v0.1-week-01-baseline.md](releases/v0.1-week-01-baseline.md).

## New Fellow Workflow

Clone the repository:

```bash
git clone https://github.com/Flow-Research/local-first-AI.git
cd local-first-AI
```

The coordinator creates the Week 1 integration branch from the baseline:

```bash
git checkout baseline/week-01-starter
git checkout -b weeks/month-01-week-01
git push -u origin weeks/month-01-week-01
```

Each fellow then branches from the weekly integration branch:

```bash
git checkout weeks/month-01-week-01
git checkout -b fellows/<github-username>/month-01-week-01-setup
```

## Alternative: Start From The Tag

Use the tag when the coordinator needs to create the weekly branch from the exact immutable snapshot:

```bash
git checkout v0.1-week-01-baseline
git checkout -b weeks/month-01-week-01
```

## Ongoing Fellow Workflow

For each later week, create a new fellow branch from the matching weekly branch:

```text
fellows/<github-username>/month-01-week-01-setup
fellows/<github-username>/month-01-week-02-local-storage
fellows/<github-username>/month-01-week-03-local-ai-flow
```

Shared project work still uses the normal branch types:

```text
feature/month-XX-week-YY-topic
research/month-XX-topic
design/month-XX-topic
docs/topic
fix/topic
```

## Protection Rule

Do not commit new work directly to:

- `master`
- `weeks/month-XX-week-YY`
- `baseline/week-01-starter`

`baseline/week-01-starter` should only change if the fellowship deliberately decides to publish a new starter baseline.

## Recommended GitHub Settings

In GitHub branch protection settings:

- Protect `master`.
- Protect `weeks/**`.
- Protect `baseline/week-01-starter`.
- Require pull requests before merging into `master`.
- Require pull requests and the `fellow-contribution-check` before merging fellow work into a weekly branch.
- Prevent force pushes.
- Prevent deletion of protected branches.

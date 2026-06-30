# Baseline Start Guide

This project keeps `master` as the evolving stable project, while `baseline/week-01-starter` stays as the clean Week 1 starter point for new fellows.

## Branch And Tag Roles

| Name | Type | Purpose |
|---|---|---|
| `master` | Branch | Evolving stable project branch |
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

Start from the Week 1 baseline:

```bash
git checkout baseline/week-01-starter
git checkout -b fellows/<github-username>/month-01-week-01-setup
```

Example:

```bash
git checkout baseline/week-01-starter
git checkout -b fellows/ada/month-01-week-01-setup
```

## Alternative: Start From The Tag

Use the tag when you want the exact immutable snapshot:

```bash
git checkout v0.1-week-01-baseline
git checkout -b fellows/<github-username>/month-01-week-01-setup
```

## Ongoing Fellow Workflow

After Week 1, a fellow can continue their own sequence:

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
- `baseline/week-01-starter`

`baseline/week-01-starter` should only change if the fellowship deliberately decides to publish a new starter baseline.

## Recommended GitHub Settings

In GitHub branch protection settings:

- Protect `master`.
- Protect `baseline/week-01-starter`.
- Require pull requests before merging into `master`.
- Prevent force pushes.
- Prevent deletion of protected branches.

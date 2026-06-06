# Benchmarking Architecture

## Purpose

The benchmarking architecture measures whether the local-first base layer works reliably on the selected compute target.

## Month 1 Benchmark Scope

Month 1 benchmarks should test:

- Local data storage
- Offline access
- Create/read/update/delete latency
- Database size
- Restart recovery
- Error count

## Simple Architecture

```text
User/Test Command
  |
Benchmark Runner
  |
Local App Logic
  |
SQLite Database
  |
Benchmark Logger
  |
Result Report
```

## Starter Metrics

| Metric | Meaning |
|---|---|
| Create latency | Time to save a new note |
| Read latency | Time to retrieve saved notes |
| Update latency | Time to edit a note |
| Delete latency | Time to remove a note |
| Database size | Size of the local database file |
| Offline success | Whether the system works without internet |
| Restart recovery | Whether data remains after app restart |
| Error count | Number of failed operations |

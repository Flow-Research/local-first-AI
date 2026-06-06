# Roadmap

This roadmap supports a 12-month research, design, and build process. Each week should produce:

- A build outcome: the smallest working technical output.
- A design outcome: a sketch, decision, diagram, prototype note, or evaluation artifact.
- A learning outcome: notes from one paper, article, or official technical source.
- A weekly report: the public learning journal for that week.

## Monthly Summary

| Month | Theme | Goal | Main Output |
|---|---|---|---|
| Month 1 | Setup and Base Layer | Define the project and create the local-first foundation | Repo structure, docs, reports, and basic app entry point |
| Month 2 | Local AI | Connect local data to a simple AI workflow | Notes prepared as local AI context |
| Month 3 | Clarity Demo | Build a clear demo showing why local-first AI matters | Demonstrable local-first assistant flow |
| Month 4 | Constraints | Test storage, latency, memory, and offline limits | Constraint report and benchmark results |
| Month 5 | Sync Thinking | Explore sync without breaking local-first principles | Sync design notes and small prototype |
| Month 6 | Privacy and Security | Study local privacy, data ownership, and safe defaults | Privacy notes and safer local storage decisions |
| Month 7 | Device Targeting | Prepare the system for a smaller device or edge target | Device target plan and compatibility notes |
| Month 8 | Local Network Use | Explore local network workflows between trusted devices | Local network experiment and report |
| Month 9 | Agent Workflow | Add a small task-oriented assistant flow | Simple local agent workflow |
| Month 10 | Evaluation | Measure usefulness, reliability, and user experience | Evaluation checklist and results |
| Month 11 | Polish | Improve docs, demo flow, errors, and presentation | Cleaner demo and public-facing documentation |
| Month 12 | Final Review | Review the full year and define the next direction | Final report, lessons learned, and next roadmap |

## Weekly Research, Design, And Build Plan

| Month | Week | Build Outcome | Design Outcome | Learn / Read |
|---|---|---|---|---|
| 1 | 1 | Create repo structure and first report | Project framing diagram | [Local-first software](https://www.inkandswitch.com/essay/local-first/) |
| 1 | 2 | Add SQLite storage layer | Data model sketch | [SQLite Architecture](https://www.sqlite.org/arch.html) |
| 1 | 3 | Add CLI app flow | User flow diagram | [Design Science in IS Research](https://damien.house/sites/default/files/Hevner-et-al-MISQ-2004.pdf) |
| 1 | 4 | Add benchmark runner | Month 1 system diagram | [Atomic Commit in SQLite](https://www.sqlite.org/atomiccommit.html) |
| 2 | 1 | Prepare local notes as context | Context packet design | [Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401) |
| 2 | 2 | Add simple AI or simulated AI response | Prompt and response flow | [REALM](https://arxiv.org/abs/2002.08909) |
| 2 | 3 | Improve retrieval and formatting | Retrieval pipeline diagram | [DPR](https://arxiv.org/abs/2004.04906) |
| 2 | 4 | Review local AI limits | Local AI limitation note | [Model Cards](https://arxiv.org/abs/1810.03993) |
| 3 | 1 | Choose demo scenario | Demo storyboard | [Local-first software](https://martin.kleppmann.com/papers/local-first.pdf) |
| 3 | 2 | Build demo path | Happy-path interaction design | [Design Science in IS Research](https://damien.house/sites/default/files/Hevner-et-al-MISQ-2004.pdf) |
| 3 | 3 | Add screenshots and usage notes | Evidence checklist | [Model Cards](https://arxiv.org/abs/1810.03993) |
| 3 | 4 | Review demo | Demo critique and next-design note | [Stochastic Parrots](https://doi.org/10.1145/3442188.3445922) |
| 4 | 1 | Define benchmark scope | Benchmark architecture diagram | [How SQLite Is Tested](https://www.sqlite.org/testing.html) |
| 4 | 2 | Run storage benchmarks | Metrics table design | [SQLite Transactions](https://www.sqlite.org/lang_transaction.html) |
| 4 | 3 | Measure resource limits | Constraint map | [SQLite File Format](https://www.sqlite.org/fileformat.html) |
| 4 | 4 | Write constraint review | Risk and constraint matrix | [Atomic Commit in SQLite](https://www.sqlite.org/atomiccommit.html) |
| 5 | 1 | Define sync principles | Sync boundary diagram | [Automerge](https://automerge.org/) |
| 5 | 2 | Document conflict cases | Conflict-resolution table | [A comprehensive study of CRDTs](https://hal.inria.fr/inria-00555588/document) |
| 5 | 3 | Build or simulate sync prototype | Sync sequence diagram | [Dynamo](https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store) |
| 5 | 4 | Review sync lessons | Sync decision record | [Local-first software](https://martin.kleppmann.com/papers/local-first.pdf) |
| 6 | 1 | Define privacy model | Data inventory table | [Stochastic Parrots](https://doi.org/10.1145/3442188.3445922) |
| 6 | 2 | Decide secret handling | Threat model sketch | [Model Cards](https://arxiv.org/abs/1810.03993) |
| 6 | 3 | Update safer defaults | Privacy checklist | [Datasheets for Datasets](https://arxiv.org/abs/1803.09010) |
| 6 | 4 | Write privacy review | Privacy decision record | [Local-first software](https://www.inkandswitch.com/essay/local-first/) |
| 7 | 1 | Choose device target | Device comparison table | [MobileNets](https://arxiv.org/abs/1704.04861) |
| 7 | 2 | Prepare device setup notes | Setup checklist | [ShuffleNet](https://arxiv.org/abs/1707.01083) |
| 7 | 3 | Run compatibility check | Compatibility matrix | [TinyML preview](https://tinymlbook.com/wp-content/uploads/2020/11/TinyML_preview.pdf) |
| 7 | 4 | Document device limits | Device constraint report | [MobileNets](https://arxiv.org/abs/1704.04861) |
| 8 | 1 | Define local network use case | Trusted device model | [Dynamo](https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store) |
| 8 | 2 | Sketch data exchange | Data exchange diagram | [Automerge](https://automerge.org/) |
| 8 | 3 | Build network experiment | Network sequence diagram | [A comprehensive study of CRDTs](https://hal.inria.fr/inria-00555588/document) |
| 8 | 4 | Review network tradeoffs | Local network risk table | [Local-first software](https://martin.kleppmann.com/papers/local-first.pdf) |
| 9 | 1 | Choose one agent task | Task boundary note | [ReAct](https://arxiv.org/abs/2210.03629) |
| 9 | 2 | Design agent flow | Input-action-output diagram | [Toolformer](https://arxiv.org/abs/2302.04761) |
| 9 | 3 | Build agent prototype | Agent trace format | [RAG](https://arxiv.org/abs/2005.11401) |
| 9 | 4 | Review agent usefulness | Agent risk and limit note | [Stochastic Parrots](https://doi.org/10.1145/3442188.3445922) |
| 10 | 1 | Define evaluation criteria | Evaluation rubric | [Model Cards](https://arxiv.org/abs/1810.03993) |
| 10 | 2 | Test reliability | Reliability checklist | [How SQLite Is Tested](https://www.sqlite.org/testing.html) |
| 10 | 3 | Review user experience | UX issue list | [Heuristic Evaluation](https://dl.acm.org/doi/10.1145/97243.97281) |
| 10 | 4 | Write evaluation report | Evaluation summary table | [Datasheets for Datasets](https://arxiv.org/abs/1803.09010) |
| 11 | 1 | Polish documentation | Documentation map | [Design Science in IS Research](https://damien.house/sites/default/files/Hevner-et-al-MISQ-2004.pdf) |
| 11 | 2 | Polish demo | Demo script | [Local-first software](https://www.inkandswitch.com/essay/local-first/) |
| 11 | 3 | Polish evidence | Evidence index | [Model Cards](https://arxiv.org/abs/1810.03993) |
| 11 | 4 | Prepare public review | Review checklist | [Stochastic Parrots](https://doi.org/10.1145/3442188.3445922) |
| 12 | 1 | Review all reports | Year evidence map | [Design Science in IS Research](https://damien.house/sites/default/files/Hevner-et-al-MISQ-2004.pdf) |
| 12 | 2 | Summarize lessons learned | Lessons matrix | [Local-first software](https://martin.kleppmann.com/papers/local-first.pdf) |
| 12 | 3 | Decide next roadmap | Next-roadmap options | [Dynamo](https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store) |
| 12 | 4 | Publish final report | Final architecture and research summary | [Model Cards](https://arxiv.org/abs/1810.03993) |

## Weekly Deliverable Rule

Do not merge a weekly branch back into `master` unless it has:

- A weekly report in `reports/month-XX/`.
- A feature or research note when the week changes behavior or design.
- Updated docs when the architecture, storage model, or project direction changes.
- Evidence in `assets/`, `benchmarks/`, or the weekly report.

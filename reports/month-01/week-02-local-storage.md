# Month 1 Week 2: Local Storage Layer

Add one block for every fellow who contributed. Keep each block short.

## Fellow 3: John Tolulope Afariogun

- **Topic:** Search / Retrieve Context for Inference
- **What I did:** I implemented the `search and prompt-preparation` APIs for the Local Context Store. It uses SQLite's `LIKE` operator to search across titles and content, pushes limits directly to the database, and orders results by importance and recency before formatting them into an LLM-ready text block. I verified it with the built-in timing demo script and learned that effective local-first AI memory relies just as much on efficiently ranking and structuring data as it does on finding keyword matches.
- **Public output:** [Powering Local-First AI: Searching and Retrieving Context for Inference](https://dev.to/john_afariogun_e2351c78af/powering-local-first-ai-searching-and-retrieving-context-for-inference-3ohl)
## Fellow 1: Alain Chan

- **Topic:** Capture / Create Context
- **What I did:** I implemented the `create_context_item` API for the Local Context Store. It validates context type, title, content, source, tags, and importance before saving a new context item into SQLite. I verified it with the Week 2 storage test script and learned that useful local-first AI memory starts with clean, structured context capture.
- **Public output:** [Why Local-First AI Starts With Good Context Capture](https://dev.to/alaindevs/why-local-first-ai-starts-with-good-context-capture-3d9g) - Dev.to


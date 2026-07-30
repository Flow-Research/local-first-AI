# Month 1 Week 3: Simple App Flow

Add one block for every fellow who contributed. Keep each block short.

## Fellow 1: Full Name

- **Topic:** Topic worked on
- **What I did:** Describe the work you completed, the result you achieved, how you verified it, one challenge you addressed, and the main lesson you learned this week. Use at least 20 words.
- **Public output:** [Post title](https://example.com/post) - Medium, X, LinkedIn, or another public platform

## Fellow 2: Alain Chan

- **Topic:** Week 3 interactive chat / local inference app flow
- **What I did:** I built the Week 3 model-first chat CLI that wires the Week 2 SQLite context store to a local OpenAI-compatible endpoint. The model chooses plain chat or tool calls (list / search / read / create / update / delete) with confirmation on writes; I verified the flow offline with the injectable storage backend and fake client tests, and learned that inference work starts with product constraints, metrics (TTFT, decode, E2E), and the right layer (runtime vs infrastructure vs tooling), not blind speed tweaks.
- **Public output:** [What I Learned from Inference Engineering Chapters 0 and 1](https://dev.to/alaindevs/what-i-learned-from-inference-engineering-chapters-0-and-1-1lja)
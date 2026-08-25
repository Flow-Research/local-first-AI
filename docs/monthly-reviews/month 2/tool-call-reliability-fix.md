# Month 2 Review: Reliable Tool-Call Recovery

## Summary

The local assistant uses model-generated tool calls to read and modify its
SQLite context store. The reliability problem was that a model could receive a
request such as “What is stored?” or “Remember that we use SQLite” and return a
plain-text response instead of the required structured tool call. A plain-text
answer to a local-data question is not grounded in the database, while a
plain-text acknowledgement of a write can claim success without saving
anything.

The fix adds a bounded recovery path. The assistant still gives the model its
normal freedom with `tool_choice="auto"`, but it now recognizes requests that
require local-data access. If the first response omits a structured tool call,
the assistant retries exactly once with `tool_choice="required"`, validates the
result, and only then executes the tool.

This review is maintained on a documentation branch based on
`feature/month-02-week-03-llama-cpp-qwen-endpoint`. The implementation being
reviewed lives in Alain’s `bugfix/tool-call-reliability` branch at commit
`7268b752797eb24062a52f0eed6f4529d7c85993`; implementation links below point
to that immutable commit.

## Original Behavior

The assistant already supplied the six context tools to every model request:

- Read tools: `search_context_items`, `get_context_item`, and
  `list_context_items`.
- Write tools: `create_context_item`, `update_context_item`, and
  `delete_context_item`.

However, `tool_choice="auto"` allows the model to answer without calling one of
those tools. This is appropriate for greetings and ordinary conversation, but
not for requests that depend on the local context store.

For example, the model could answer “I cannot access that” when asked “What is
stored?” even though the list tool was available. It could also say “I will
remember that” without creating a database record.

## What Was Changed

### 1. Tool choice became configurable

`_obtain_response()` now accepts a `tool_choice` argument with an `"auto"`
default. The value is forwarded to the OpenAI-compatible chat completion
request. Normal model calls therefore preserve the existing behavior, while a
recovery call can explicitly use `tool_choice="required"`.

Reference: [`_obtain_response()` in `app.py`](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/src/python/local_first_ai/assistant/app.py#L720)

### 2. Requests are classified by required tool family

`_required_tool_family()` inspects the most recent user message and returns one
of three results:

- `READ_TOOLS` for requests about stored notes, local context, decisions,
  keywords, or lists of stored items.
- `WRITE_TOOLS` for requests to remember, save, record, update, change, or
  delete local data.
- `None` for normal conversation that should remain model-controlled.

The classification is intentionally at the family level. The recovery logic
does not decide whether a read request needs `search_context_items` or
`list_context_items`; the model still selects the specific tool.

The function also avoids known false positives. For example, “Save me a seat”
is not interpreted as a database write, and an ordinary retail-store question
does not automatically become a local-context read.

Reference: [`_required_tool_family()` in `app.py`](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/src/python/local_first_ai/assistant/app.py#L758)

### 3. Missing tool calls receive one repair attempt

At the beginning of `run_assistant_turn()`, the assistant determines whether a
tool family is required and initializes two state flags:

- `repair_attempted` prevents repeated repair requests.
- `structured_call_seen` records whether the model has already returned a
  valid structured call.

If a required request produces no structured tool call, the assistant makes a
non-streaming recovery request with `tool_choice="required"`. The retry is
limited to one attempt, so an uncooperative or incompatible model cannot cause
an unbounded loop.

References:

- [Recovery state in `run_assistant_turn()`](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/src/python/local_first_ai/assistant/app.py#L808)
- [One-time required-tool retry](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/src/python/local_first_ai/assistant/app.py#L854)

### 4. Recovered tools are validated before execution

Requiring a tool does not guarantee that the model will select an appropriate
one. After recovery, the assistant checks that:

- At least one structured tool call exists.
- Every returned tool belongs to the required family.

For example, a request to read stored data must not recover with
`create_context_item`. If the recovery is missing or from the wrong family,
the turn fails closed with a runtime error and no tool is executed.

Reference: [Recovered-tool validation](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/src/python/local_first_ai/assistant/app.py#L865)

### 5. Ungrounded streamed text is withheld

Streaming creates an additional risk: the first response may begin printing an
ungrounded answer before the assistant discovers that the required tool was
omitted. For the first streamed response of a tool-required request, the token
callback is temporarily withheld. If recovery is necessary, the original text
is discarded. Once the tool has run, only the final grounded answer is shown.

Reference: [Initial stream holdback](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/src/python/local_first_ai/assistant/app.py#L813)

### 6. Existing duplicate-write protection is preserved

The tool loop fingerprints completed writes and reuses their previous result if
the same write is returned again. The recovery path feeds into this existing
execution flow, ensuring a repaired create, update, or delete operation cannot
silently perform the same mutation twice within one assistant turn.

Reference: [Write fingerprint check](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/src/python/local_first_ai/assistant/app.py#L904)

## Resulting Flow

```text
User request
    |
    v
Does the request require local-data tools?
    | no                         | yes
    v                            v
Normal auto response       First response with tool_choice="auto"
                                 |
                     +-----------+-----------+
                     |                       |
              Tool call returned       Tool call omitted
                     |                       |
                     v                       v
              Validate/execute      Retry once with
                                   tool_choice="required"
                                             |
                                  +----------+----------+
                                  |                     |
                            Correct family       Missing/wrong family
                                  |                     |
                                  v                     v
                           Execute safely          Fail closed
```

## Verification

Automated tests were added for the following cases:

1. A missing read call is repaired once, after which the assistant lists the
   stored item.
2. A missing write call is repaired and creates exactly one database record.
3. A repair with no tool or a tool from the wrong family fails without changing
   storage.
4. The final plain-text answer after successful tool execution is not mistaken
   for another missing tool call.
5. Greetings and “Save me a seat” remain ordinary conversation.
6. Explicit local-note questions consistently trigger read recovery.
7. “What store sells shoes?” remains an ordinary question rather than a local
   database request.
8. Streaming discards the initial ungrounded text and emits only the final
   grounded answer.

Test references:

- [Read recovery test](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/tests/python/test_assistant.py#L353)
- [Write recovery and single-mutation test](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/tests/python/test_assistant.py#L375)
- [Wrong-family fail-closed test](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/tests/python/test_assistant.py#L406)
- [Streaming recovery test](https://github.com/AlainDevs/local-first-AI/blob/7268b752797eb24062a52f0eed6f4529d7c85993/tests/python/test_assistant.py#L1125)

The contribution was recorded as commit
`7268b752797eb24062a52f0eed6f4529d7c85993` with the subject
`fix: improve tool call reliability and add automated tests for repairs`.

## Design Trade-offs and Limitations

- The classifier uses explicit text patterns rather than a general intent
  classifier. This keeps the recovery deterministic and offline, but new user
  phrasings may require additional patterns.
- `tool_choice="required"` requires the selected inference server and model to
  support structured OpenAI-compatible tool calling.
- Recovery validates the tool family, not the semantic quality of every model
  argument. The existing argument-validation layer remains responsible for
  rejecting malformed IDs, invalid context types, bad importance values, and
  malformed JSON.
- Only one repair is attempted. This favors predictable behavior and prevents
  loops, but a model that fails the repair does not receive another chance in
  the same turn.

## Outcome

The assistant remains conversational for ordinary prompts while becoming more
dependable for local-data requests. Read answers are more likely to be grounded
in SQLite results, write acknowledgements correspond to actual confirmed
mutations, invalid recovery calls fail safely, and streamed output no longer
exposes discarded ungrounded text.

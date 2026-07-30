"""Week 3 interactive chat CLI wired to the local context store."""

from local_first_ai.assistant.app import (
    MODEL_UNAVAILABLE_MESSAGE,
    ChatSession,
    Config,
    StorageBackend,
    build_parser,
    execute_tool,
    main,
    make_client,
    run_assistant_turn,
    validate_tool_args,
)

__all__ = [
    "MODEL_UNAVAILABLE_MESSAGE",
    "ChatSession",
    "Config",
    "StorageBackend",
    "build_parser",
    "execute_tool",
    "main",
    "make_client",
    "run_assistant_turn",
    "validate_tool_args",
]

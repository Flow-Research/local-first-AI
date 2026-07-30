"""Allow ``python -m local_first_ai.assistant`` from ``src/python`` on PYTHONPATH."""

from local_first_ai.assistant.app import main

raise SystemExit(main())

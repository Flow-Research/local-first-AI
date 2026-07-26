"""Backward-compatible entry for Week 3 assistant.

Prefer: ``PYTHONPATH=src/python python -m local_first_ai.assistant``
"""

from __future__ import annotations

import sys

from local_first_ai.assistant import app as _app

sys.modules[__name__] = _app

if __name__ == "__main__":
    raise SystemExit(_app.main())

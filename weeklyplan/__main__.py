"""允许通过 ``python -m weeklyplan`` 运行。"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.full_chain_p0_repairs.run_full_chain_p0_regression_v1 import main


if __name__ == "__main__":
    raise SystemExit(main())

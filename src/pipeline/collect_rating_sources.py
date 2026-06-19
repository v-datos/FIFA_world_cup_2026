"""CLI entrypoint for the T-039 no-cost rating source spike."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.analytics.rating_sources import main


if __name__ == "__main__":
    main()

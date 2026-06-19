"""CLI entrypoint for the T-038 squad/style source cache manifest."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.analytics.squad_style_sources import main


if __name__ == "__main__":
    main()

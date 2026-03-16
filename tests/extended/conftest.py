"""
Pytest configuration for Extended SDK tests.

Adds the project root to sys.path to ensure extended module is importable.
"""

import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import fixtures from fixtures module
from tests.extended.fixtures import *  # noqa: F401, F403

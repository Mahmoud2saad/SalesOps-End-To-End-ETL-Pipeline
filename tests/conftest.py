"""
Makes the dev_code script folders importable as modules during tests,
without needing to restructure the actual pipeline layout. Real projects
would eventually promote dev_code/1) Scripts/{audit,quality} to a proper
installable package; this is the pragmatic middle ground for now.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "dev_code" / "1) Scripts"

for subfolder in ["audit", "quality"]:
    path = str(SCRIPTS_DIR / subfolder)
    if path not in sys.path:
        sys.path.insert(0, path)

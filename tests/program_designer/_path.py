"""Put the program designer's scripts/ on sys.path so tests import lib.* the way designer.py does."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "plugins" / "ironledger" / "skills" / "ironledger-program-designer"
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

"""Build the controlled 850→1000 shortlist without touching the 850 review files."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts.build_manual_850_selection as builder

builder.OUTPUT = ROOT / "data/research/manual-expansion-1000-selection.json"
builder.LOGO_REPORT = ROOT / "reports/manual-expansion-1000-logo-import.json"
builder.LOGO_BLOCKLIST = ROOT / "data/research/manual-expansion-1000-logo-blocklist.json"

if __name__ == "__main__":
    builder.main()

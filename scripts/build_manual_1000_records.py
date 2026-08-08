"""Build schema-complete records 851..1000 from the controlled shortlist."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts.build_manual_850_records as builder

builder.SELECTION = ROOT / "data/research/manual-expansion-1000-selection.json"
builder.OUTPUT = ROOT / "data/research/manual-expansion-1000-records.json"

if __name__ == "__main__":
    builder.main()

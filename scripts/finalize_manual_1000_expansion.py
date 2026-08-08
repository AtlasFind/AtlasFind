"""Run the release-gated 850→1000 finalizer with isolated review files."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts.finalize_manual_850_expansion as finalizer

finalizer.STAGING = ROOT / "data/research/manual-expansion-1000-records.json"
finalizer.SOURCE_AUDIT = ROOT / "reports/manual-expansion-1000-source-audit.json"
finalizer.LOGO_AUDIT = ROOT / "reports/manual-expansion-1000-logo-import.json"

if __name__ == "__main__":
    finalizer.main()

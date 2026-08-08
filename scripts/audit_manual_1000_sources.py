"""Audit the official website and repository for records 851..1000."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts.audit_manual_850_sources as auditor

auditor.RECORDS = ROOT / "data/research/manual-expansion-1000-records.json"
auditor.REPORT = ROOT / "reports/manual-expansion-1000-source-audit.json"

if __name__ == "__main__":
    auditor.main()

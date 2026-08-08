"""Import official local logos for records 851..1000."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scripts.import_manual_850_logos as importer

importer.RECORDS = ROOT / "data/research/manual-expansion-1000-records.json"
importer.REPORT = ROOT / "reports/manual-expansion-1000-logo-import.json"

if __name__ == "__main__":
    importer.main()

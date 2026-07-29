from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_ROOT = ROOT / "static" / "images" / "tools"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        from PIL import Image
    except ImportError:
        print("Pillow is required. Run: pip install -r requirements.txt")
        return 1
    files = [p for p in IMAGE_ROOT.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    changed = 0
    for path in files:
        target = path.with_suffix(".webp")
        if target.exists() and target.stat().st_mtime_ns >= path.stat().st_mtime_ns:
            continue
        print(f"{'Would optimize' if args.dry_run else 'Optimizing'}: {path.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
        if not args.dry_run:
            with Image.open(path) as image:
                image.thumbnail((1024, 1024))
                image.save(target, "WEBP", quality=88, method=6)
        changed += 1
    print(f"Candidates: {len(files)}; {'planned' if args.dry_run else 'written'}: {changed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

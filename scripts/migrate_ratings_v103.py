from __future__ import annotations
import argparse, json
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CATALOG = BASE / "data" / "catalog"
BACKUP = BASE / "data" / "backups" / "ratings-v102-before-v103.json"

CRITERIA = ("features","ease_of_use","value","performance","security","platforms","support","transparency")

def pending_rating(tool):
    old_score = tool.get("rating")
    old_source = tool.get("rating_source")
    return {
        "status":"unreviewed",
        "overall_score":None,
        "scale":10,
        "methodology_version":"1.0.0",
        "category_profile":"default",
        "confidence_score":0,
        "confidence_level":"insufficient",
        "reviewed_at":None,
        "next_review_at":None,
        "reviewed_by":None,
        "approved_by":None,
        "criteria":{key:{"score":None,"weight":None,"reason_tr":"","reason_en":"","evidence_ids":[],"status":"insufficient_data"} for key in CRITERIA},
        "editor_summary_tr":"",
        "editor_summary_en":"",
        "sources":[],
        "external_ratings":[],
        "user_rating":{"score":None,"review_count":0,"verified_count":0},
        "change_history":[],
        "legacy": {"score": old_score, "scale": 5, "source": old_source, "displayed": False}
    }

def main(apply=False):
    files=[p for p in CATALOG.glob("*.json") if p.name != "manifest.json"]
    all_backup=[]; converted=0
    for path in files:
        items=json.loads(path.read_text(encoding="utf-8"))
        changed=False
        for tool in items:
            all_backup.append({"id":tool.get("id"),"slug":tool.get("slug"),"rating":tool.get("rating"),"rating_source":tool.get("rating_source")})
            if "rating_v103" not in tool:
                tool["rating_v103"]=pending_rating(tool); converted+=1; changed=True
            tool["rating"]=0
            tool["rating_source"]="not-rated"
        if apply and changed:
            path.write_text(json.dumps(items,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if apply:
        BACKUP.parent.mkdir(parents=True,exist_ok=True)
        BACKUP.write_text(json.dumps(all_backup,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Detected tools: {len(all_backup)}")
    print(f"Converted tools: {converted}")
    print("Mode:", "APPLIED" if apply else "DRY RUN")

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--apply",action="store_true")
    main(parser.parse_args().apply)

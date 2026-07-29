from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from catalog.loader import load_catalog
from services.rating_service import evaluate_rating
from validators.rating_validator import validate_rating_profiles

def main():
    errors=validate_rating_profiles(); tools=load_catalog(validate=True)
    legacy_visible=0; published=0; pending=0
    for tool in tools:
        rating=tool.get('rating_v103')
        if not isinstance(rating,dict): errors.append(f"{tool.get('slug')}: rating_v103 missing"); continue
        if tool.get('rating_source') not in {'not-rated','atlasfind_v103'}: legacy_visible+=1
        result=evaluate_rating(rating,tool.get('category',''))
        if result.publishable: published+=1
        else: pending+=1
        if rating.get('status')=='published' and not result.publishable: errors.append(f"{tool.get('slug')}: invalid published rating")
    if legacy_visible: errors.append(f"{legacy_visible} legacy scores are still visible")
    if errors:
        print('v1.0.3 rating validation failed:'); [print('-',e) for e in errors]; raise SystemExit(1)
    print(f"Rating validation successful: {len(tools)} tools, {published} published, {pending} pending")
    print('Legacy unverified scores visible: 0')
if __name__=='__main__': main()

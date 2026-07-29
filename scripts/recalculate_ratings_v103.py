from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from catalog.loader import load_catalog
from services.rating_service import evaluate_rating

def main():
    tools=load_catalog(validate=True); publishable=0
    for tool in tools:
        result=evaluate_rating(tool.get('rating_v103') or {},tool.get('category',''))
        publishable += int(result.publishable)
    print(f"Recalculation completed: {len(tools)} tools, {publishable} publishable ratings")
if __name__=='__main__': main()

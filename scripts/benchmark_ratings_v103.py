from pathlib import Path
import sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from services.rating_service import evaluate_rating,bayesian_user_score
from catalog.loader import load_catalog

def main():
    base=(load_catalog(validate=True)[0].get('rating_v103') or {})
    for count in (100,1000,5000,10000):
        started=time.perf_counter()
        for _ in range(count): evaluate_rating(base,'')
        elapsed=(time.perf_counter()-started)*1000
        print(f"{count:>5} rating calculations: {elapsed:.2f} ms")
    started=time.perf_counter()
    for i in range(100000): bayesian_user_score(8.2*(i%100+1),i%100+1)
    print(f"100000 user aggregates: {(time.perf_counter()-started)*1000:.2f} ms")
if __name__=='__main__':main()

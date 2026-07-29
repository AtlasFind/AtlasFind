from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main() -> int:
    parser=argparse.ArgumentParser(description='Approve or reject one discovered logo candidate.')
    parser.add_argument('slug')
    parser.add_argument('candidate_index',type=int)
    parser.add_argument('--decision',choices=('approved','rejected'),required=True)
    parser.add_argument('--license-status',default='brand_usage')
    parser.add_argument('--light',choices=('yes','no'),default='yes')
    parser.add_argument('--dark',choices=('yes','no'),default='yes')
    parser.add_argument('--notes',default='')
    parser.add_argument('--queue',default='data/branding/logo-queue.json')
    args=parser.parse_args()
    path=ROOT/args.queue; payload=json.loads(path.read_text(encoding='utf-8'))
    item=next((row for row in payload['items'] if row.get('slug')==args.slug),None)
    if item is None: raise SystemExit(f'Tool not found in queue: {args.slug}')
    candidates=item.get('candidates',[])
    if args.candidate_index<0 or args.candidate_index>=len(candidates):
        raise SystemExit(f'Candidate index must be between 0 and {max(0,len(candidates)-1)}')
    if args.decision=='approved':
        for candidate in candidates: candidate['review_status']='rejected'
    candidate=candidates[args.candidate_index]
    candidate.update({
        'review_status':args.decision,
        'license_status':args.license_status,
        'supports_light_theme':args.light=='yes',
        'supports_dark_theme':args.dark=='yes',
        'notes':args.notes,
    })
    item['status']='approved' if args.decision=='approved' else 'review'
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"{args.slug} candidate #{args.candidate_index}: {args.decision}")
    print(candidate['url'])
    return 0
if __name__=='__main__': raise SystemExit(main())

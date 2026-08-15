from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app, load_articles, load_tools, CATEGORY_INFO, COLLECTION_INFO

paths=['/','/guides','/recommend','/robots.txt','/sitemap.xml']
paths += [f"/tools/{t['slug']}" for t in load_tools()]
paths += [f"/guides/{a['slug']}" for a in load_articles()]
paths += [f"/categories/{s}" for s in CATEGORY_INFO]
paths += [f"/collections/{s}" for s in COLLECTION_INFO]
errors=[]
with app.test_client() as client:
    for path in paths:
        # Public, non-localized URLs intentionally redirect to the visitor's
        # language. Follow that canonical redirect so this check validates the
        # destination page instead of reporting healthy 301 responses as errors.
        response=client.get(path, follow_redirects=True)
        if response.status_code != 200:
            errors.append(f'{path}: {response.status_code}')
if errors:
    print('\n'.join(errors)); raise SystemExit(1)
print(f'Internal link check successful: {len(paths)} public URLs returned 200.')

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, load_articles, load_tools
from seo import SITE_URL, article_schema, faq_schema, software_schema

errors=[]
if not SITE_URL.startswith(('http://','https://')):
    errors.append('SITE_URL must be absolute')
for tool in load_tools():
    schema=software_schema(tool)
    if not schema.get('name') or not schema.get('url'):
        errors.append(f"Invalid software schema: {tool.get('slug')}")
for article in load_articles():
    schema=article_schema(article)
    if not schema.get('headline') or not schema.get('mainEntityOfPage'):
        errors.append(f"Invalid article schema: {article.get('slug')}")
    faq=faq_schema(article.get('faq',[]))
    if article.get('faq') and not faq:
        errors.append(f"Invalid FAQ schema: {article.get('slug')}")
with app.test_client() as client:
    robots=client.get('/robots.txt')
    sitemap=client.get('/sitemap.xml')
    if robots.status_code != 200 or '/admin/' not in robots.get_data(as_text=True): errors.append('robots.txt invalid')
    if sitemap.status_code != 200 or '<urlset' not in sitemap.get_data(as_text=True): errors.append('sitemap.xml invalid')
if errors:
    print('\n'.join(f'- {e}' for e in errors)); raise SystemExit(1)
print(f'SEO validation successful: {len(load_tools())} tools and {len(load_articles())} articles checked for v0.6.0.')

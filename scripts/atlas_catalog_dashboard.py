"""Local live dashboard and process controller for the AtlasFind catalog worker."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data/research/overnight-tool-candidates.json"
WORKER = ROOT / "scripts/atlas_catalog_worker.py"
HOST, PORT = "127.0.0.1", 8765
PROCESS: subprocess.Popen | None = None

DASHBOARD = r'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AtlasFind Katalog İşçisi</title><style>
:root{color-scheme:dark;--bg:#080914;--card:#131526;--line:#282b43;--muted:#9ba2bc;--purple:#8b5cf6;--green:#24d18f}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% 0,#241344 0,transparent 34%),var(--bg);font:14px Inter,Segoe UI,sans-serif;color:#f7f7fb}.wrap{max-width:1400px;margin:auto;padding:28px}.top{display:flex;justify-content:space-between;gap:20px;align-items:center}.brand h1{margin:0 0 8px;font-size:30px}.brand p{margin:0;color:var(--muted)}button{border:1px solid #6d3de7;background:#6d3de7;color:white;border-radius:12px;padding:12px 18px;font-weight:700;cursor:pointer}.stats{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin:24px 0}.stat{background:rgba(19,21,38,.9);border:1px solid var(--line);border-radius:16px;padding:18px}.stat b{font-size:26px;display:block;margin-bottom:6px}.stat span{color:var(--muted)}.controls{display:flex;gap:12px;margin-bottom:18px}.controls input,.controls select{background:var(--card);border:1px solid var(--line);color:white;padding:12px;border-radius:11px}.controls input{flex:1}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.tool{background:rgba(19,21,38,.94);border:1px solid var(--line);border-radius:18px;overflow:hidden}.preview{height:150px;width:100%;object-fit:cover;background:#0d0f1c}.body{padding:17px}.title{display:flex;justify-content:space-between;gap:10px}.title h2{margin:0;font-size:18px}.stars{color:#ffd76a}.desc{color:#c4c8d8;line-height:1.5;min-height:64px}.tags{display:flex;gap:7px;flex-wrap:wrap}.tag{border:1px solid #3a3d5b;border-radius:99px;padding:5px 8px;color:#bfc4d8;font-size:12px}.meta{color:var(--muted);font-size:12px;margin:12px 0}.links{display:flex;gap:10px}.links a{color:#cbb8ff;text-decoration:none}.state{display:inline-flex;gap:7px;align-items:center;color:var(--green)}.dot{width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 12px var(--green)}@media(max-width:1000px){.stats{grid-template-columns:repeat(3,1fr)}.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.grid{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}.top{align-items:flex-start;flex-direction:column}}
</style></head><body><div class="wrap"><div class="top"><div class="brand"><h1>🦆 AtlasFind Katalog İşçisi</h1><p><span class="state"><i class="dot"></i><span id="state">Çalışıyor</span></span> · Yalnızca inceleme kuyruğu, otomatik yayın yok</p></div><button onclick="stopWorker()">İşçiyi güvenle durdur</button></div><div class="stats"><div class="stat"><b id="total">0</b><span>Toplanan</span></div><div class="stat"><b id="scanned">0</b><span>Taranan</span></div><div class="stat"><b id="duplicates">0</b><span>Kopya engellendi</span></div><div class="stat"><b id="rejected">0</b><span>Eksik bilgi reddi</span></div><div class="stat"><b id="errors">0</b><span>Bağlantı hatası</span></div><div class="stat"><b id="cycles">0</b><span>Tamamlanan tur</span></div></div><div class="controls"><input id="search" placeholder="Araç, açıklama veya kategori ara..." oninput="render()"><select id="category" onchange="render()"><option value="">Tüm kategoriler</option></select></div><div class="grid" id="grid"></div></div><script>
let data={items:[],stats:{}};function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}async function refresh(){try{const r=await fetch('/api/status',{cache:'no-store'});data=await r.json();for(const k of ['scanned','duplicates','rejected','errors','cycles'])document.getElementById(k).textContent=data.stats?.[k]||0;document.getElementById('total').textContent=data.items.length;document.getElementById('state').textContent=data.running?'Çalışıyor':'Durduruldu';document.querySelector('.dot').style.background=data.running?'var(--green)':'#ff667a';categories();render()}catch(e){document.getElementById('state').textContent='Panel bağlantısı kesildi'}}function categories(){const el=document.getElementById('category'),old=el.value,c=[...new Set(data.items.map(x=>x.category_suggestion))].sort();el.innerHTML='<option value="">Tüm kategoriler</option>'+c.map(x=>`<option>${esc(x)}</option>`).join('');el.value=old}function render(){const q=document.getElementById('search').value.toLowerCase(),cat=document.getElementById('category').value;const items=data.items.filter(x=>(!cat||x.category_suggestion===cat)&&JSON.stringify(x).toLowerCase().includes(q)).slice().reverse();document.getElementById('grid').innerHTML=items.map(x=>`<article class="tool"><img class="preview" loading="lazy" src="${esc(x.image_url)}" alt="${esc(x.name)} görseli"><div class="body"><div class="title"><h2>${esc(x.name)}</h2><span class="stars">★ ${Number(x.stars||0).toLocaleString('tr-TR')}</span></div><p class="desc">${esc(x.description_source_text)}</p><div class="tags"><span class="tag">${esc(x.category_suggestion)}</span><span class="tag">${esc(x.subcategory_suggestion)}</span>${(x.topics||[]).slice(0,3).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div><div class="meta">Lisans: ${esc(x.license||'Belirtilmemiş')} · Durum: İnsan incelemesi bekliyor<br>Bulunma sorgusu: ${esc(x.discovery_query)}</div><div class="links"><a target="_blank" href="${esc(x.official_url)}">Resmî site ↗</a><a target="_blank" href="${esc(x.repository_url)}">Kaynak depo ↗</a></div></div></article>`).join('')||'<p>Henüz eşleşen araç yok.</p>'}async function stopWorker(){if(confirm('Katalog işçisi güvenle durdurulsun mu?'))await fetch('/api/stop',{method:'POST'});refresh()}refresh();setInterval(refresh,4000);
</script></body></html>'''


def queue_payload() -> dict:
    if QUEUE.exists():
        payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    else:
        payload = {"items": [], "stats": {}}
    payload["running"] = bool(PROCESS and PROCESS.poll() is None)
    return payload


class Handler(BaseHTTPRequestHandler):
    def send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status); self.send_header("Content-Type", content_type); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)
    def do_GET(self) -> None:
        if self.path == "/api/status": self.send(200, json.dumps(queue_payload(), ensure_ascii=False).encode(), "application/json; charset=utf-8")
        elif self.path == "/": self.send(200, DASHBOARD.encode(), "text/html; charset=utf-8")
        else: self.send(404, b"Not found", "text/plain")
    def do_POST(self) -> None:
        global PROCESS
        if self.path != "/api/stop": return self.send(404, b"Not found", "text/plain")
        if PROCESS and PROCESS.poll() is None: PROCESS.terminate()
        self.send(200, b'{"ok":true}', "application/json")
    def log_message(self, *_: object) -> None: pass


def main() -> None:
    global PROCESS
    PROCESS = subprocess.Popen([sys.executable, str(WORKER), "--hours", "0", "--max-candidates", "0", "--min-stars", "250", "--cycle-minutes", "20"], cwd=ROOT)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    if os.environ.get("ATLASFIND_NO_BROWSER") != "1":
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{HOST}:{PORT}/")).start()
    print(f"AtlasFind paneli: http://{HOST}:{PORT}/")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        if PROCESS and PROCESS.poll() is None: PROCESS.terminate()
        server.server_close()


if __name__ == "__main__": main()

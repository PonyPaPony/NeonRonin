import json, sys
sys.path.insert(0, 'tests')
from conftest import _serve, _open
from playwright.sync_api import sync_playwright
s = _serve('orig'); url = f'http://127.0.0.1:{s.server_address[1]}/index.html'
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
    ctx, page = _open(b, url)
    page.evaluate("() => { for (const c of ['unlock3','loc 3','gold 50000000','souls 5000','jade 500']) runCmd(c); S.maxZone=4; S.maxZone2=4; S.maxZone3=4; save(); }")
    d = page.evaluate("() => JSON.parse(localStorage.getItem(CFG.SAVE_KEY))")
    print('errors', page.errors, 'loc', d['loc'], 'keys', len(d))
    json.dump(d, open('tests/fixtures/save_v6.json', 'w', encoding='utf-8'), ensure_ascii=False)
    b.close()

import sys; sys.path.insert(0,'tests')
from conftest import _serve,_open
from playwright.sync_api import sync_playwright
setup = sys.argv[1] if len(sys.argv) > 1 else ''
tag = sys.argv[2] if len(sys.argv) > 2 else 'x'
s=_serve('www'); url=f'http://127.0.0.1:{s.server_address[1]}/index.html'
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    for loc in [1,2,3]:
        ctx,pg=_open(b,url, viewport={'width':1000,'height':2800}); pg.wait_for_timeout(400)
        pg.evaluate(f"() => {{ runCmd('unlock3'); travelTo({loc}); G.helpT=0; {setup} hero.x = 640; hero.y = 1560; }}")
        pg.wait_for_timeout(900); pg.screenshot(path=f'shots/base_{tag}_{loc}.png'); print(loc, pg.errors); ctx.close()

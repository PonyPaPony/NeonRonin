import sys; sys.path.insert(0,'tests')
from conftest import _serve,_open
from playwright.sync_api import sync_playwright
s=_serve('www'); url=f'http://127.0.0.1:{s.server_address[1]}/index.html'
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    ctx,pg=_open(b,url); pg.wait_for_timeout(800)
    pg.evaluate("() => { S.village.crystal=true; S.gold=1e9; S.village.steps.ratusha=2; S.village.steps.forge=1; S.unlock2=true; vStartBuild('tea'); G.vSel='forge'; openVillage(); }"); pg.wait_for_timeout(400)
    pg.screenshot(path='shots/ui_pc.png'); print(pg.errors)
    ctx2=b.new_context(service_workers='block', **p.devices['Pixel 7 landscape']); pg2=ctx2.new_page(); pg2.goto(url); pg2.wait_for_function("typeof S==='object'", polling=100)
    pg2.wait_for_timeout(800); pg2.evaluate("() => { S.village.crystal=true; S.gold=1e9; S.village.steps.ratusha=1; G.vSel='ratusha'; openVillage(); }"); pg2.wait_for_timeout(400)
    pg2.screenshot(path='shots/ui_phone.png')

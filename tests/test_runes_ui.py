"""Руны 2а, задача 7: вкладка «符 Руны» в кузнице."""
import pytest
from conftest import js, run

BASE = "runCmd('unlock3'); S.tower.unlocked = true; travelTo(3); fixSlots(); refreshStats(); S.village.peakGM = 1000; S.gold = 1e15;"
OPEN = "openForge(); G.forgeTab = 'r'; renderForge();"


def test_tab_visibility(page):
    run(page, "runCmd('unlock3'); travelTo(3); S.tower.unlocked = false; openForge();")
    assert js(page, "document.querySelector('#tab-r').classList.contains('hidden')") is True
    run(page, "closeForge(); S.tower.unlocked = true; openForge();")
    assert js(page, "document.querySelector('#tab-r').classList.contains('hidden')") is False
    run(page, "G.forgeTab = 'r'; renderForge();")
    assert js(page, "!!document.querySelector('#f-right .rgrid')") is True
    run(page, "closeForge(); S.tower.charges = 2; towerEnter(1, 1); G.forgeTab = 'r'; openForge();")
    assert js(page, "document.querySelector('#tab-r').classList.contains('hidden')") is True and js(page, "G.forgeTab") == 'w'


def test_tab_actions_flow(page):
    run(page, BASE + "S.runes.frag[0] = 10; Math.random = () => 0.3;" + OPEN)
    page.click("#forge [data-act='rforge'][data-slot='0']")
    assert js(page, "S.runes.bag.length") == 1 and js(page, "S.runes.frag[0]") == 0
    rid = js(page, "S.runes.bag[0].id"); icon = js(page, f"RUNES['{rid}'].icon")
    page.click("#forge [data-act='rbag'][data-slot='0']")
    g0 = js(page, "S.gold")
    page.click("#forge [data-act='rins'][data-item='w'][data-slot='0']")
    assert js(page, "S.runes.w[0] && S.runes.w[0].id") == rid and js(page, "S.gold") < g0
    assert icon in page.inner_text("#forge [data-act='rsel'][data-item='w'][data-slot='0']")
    page.click("#forge [data-act='rsel'][data-item='w'][data-slot='0']")
    page.click("#forge [data-act='rext']")
    assert js(page, "S.runes.w[0]") is None and js(page, "S.runes.bag.length") == 1


def test_card_shows_three_places(page):
    run(page, BASE + "S.runes.w[0] = {id:'elem', r:2, f:[0,0,0,0,0,0]}; G.runeSel = {item:'w', slot:0};" + OPEN)
    r = js(page, "[...document.querySelectorAll('#f-right .rtxt')].map(x => [x.dataset.place, x.classList.contains('on'), x.textContent])")
    assert [x[0] for x in r] == ['w', 'a', 'j']
    assert [x[1] for x in r] == [True, False, False]
    assert 'Стихия' in page.inner_text('#f-right') and all(x[2] for x in r)


def test_double_press_single_action(page):
    run(page, BASE + "S.runes.bag = [{id:'time', r:2, f:[0,0,10,0,0,0]}, {id:'shade', r:2, f:[0,0,10,0,0,0]}]; G.runeSel = {bag: 0};" + OPEN)
    page.click("#forge [data-act='rscr']")
    assert 'Точно' in page.inner_text("#forge [data-act='rscr']")
    page.wait_for_timeout(50)
    page.click("#forge [data-act='rscr']")
    assert js(page, "S.runes.bag.length") == 2                    # подлаг (второе нажатие сразу) — ничего не разобрано
    page.wait_for_timeout(500)
    page.click("#forge [data-act='rscr']")
    assert js(page, "S.runes.bag.length") == 1 and js(page, "S.runes.frag[2]") == 3
    page.click("#forge [data-act='rscr']")
    assert js(page, "S.runes.bag.length") == 1                    # следующая — снова через подтверждение
    page.wait_for_timeout(3600)
    page.click("#forge [data-act='rscr']")
    assert js(page, "S.runes.bag.length") == 1 and 'Точно' in page.inner_text("#forge [data-act='rscr']")


def test_tab_phone_layout(open_page):
    p = open_page(viewport={'width': 412, 'height': 915}, is_mobile=True, has_touch=True)
    p.evaluate("() => { " + BASE + OPEN + " }")
    hs = p.evaluate("() => [...document.querySelectorAll('#f-right .rslot')].map(b => b.getBoundingClientRect().height)")
    assert len(hs) == 9 and min(hs) >= 40
    w = p.evaluate("() => document.querySelector('#f-right .rgrid').getBoundingClientRect().width")
    assert w <= 412


def _tab_fps(browser, url, tab):
    from conftest import _open
    ctx, p = _open(browser, url); cdp = ctx.new_cdp_session(p); cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
    p.evaluate("() => { " + BASE + f" GFX.mode = 'mid'; GFX.level = 1; SET.gfx = 'mid'; document.body.classList.add('gfx-lo'); S.ring.lvl = 5; S.runes.w = [{{id:'elem',r:2,f:[0,0,0,0,0,0]}}, null, null]; openForge(); G.forgeTab = '{tab}'; renderForge(); }}")
    p.wait_for_timeout(1500)
    f = p.evaluate("() => new Promise(r => { let n = 0; const t0 = performance.now(); const k = () => { n++; if (performance.now() - t0 < 3000) requestAnimationFrame(k); else r(n / ((performance.now() - t0) / 1000)); }; requestAnimationFrame(k); })")
    ctx.close(); return f


def test_tab_fps_lo(browser, srv):
    med = lambda l: sorted(l)[1]
    fj = med([_tab_fps(browser, srv, 'j') for _ in range(3)])
    fr = med([_tab_fps(browser, srv, 'r') for _ in range(3)])
    print('fps j', fj, 'r', fr)
    assert fr >= 0.9 * fj

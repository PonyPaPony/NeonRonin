import pytest
from conftest import js, run, frames, load_save

SPY = """() => { window.__white = 0; const P = CanvasRenderingContext2D.prototype; if (window.__spy3) return; window.__spy3 = true;
  const fr = P.fill, rect = P.fillRect; const chk = function () { const s = String(this.fillStyle).toLowerCase(); if ((s === '#ffffff' || s === '#fff' || s === 'white') && this.globalAlpha > 0.3) window.__white++; };
  P.fill = function (...a) { if (window.__inE) chk.call(this); return fr.apply(this, a); }; P.fillRect = function (...a) { if (window.__inE) chk.call(this); return rect.apply(this, a); };
  for (const n of ['elemTick', 'vReact', 'drawElemIcons']) { const o = window[n]; if (!o) continue; window[n] = function (...a) { window.__inE = true; try { return o.apply(this, a); } finally { window.__inE = false; } }; } }"""
ALL = "S.w.ench = [{id:'burn',t:4,v:24}, {id:'poison',t:4,v:23}, {id:'frost',t:4,v:20}, {id:'chain',t:4,v:23}]; refreshStats();"


def test_no_white_and_slow(page):
    page.evaluate(SPY)
    run(page, ALL + " runCmd('tp 1'); toggleAuto(true); G.god = true;")
    page.wait_for_timeout(5000)
    assert js(page, "window.__white") == 0


def test_status_icons_on_enemies(page):
    run(page, ALL + " runCmd('tp 1'); toggleAuto(true); G.god = true;")
    page.wait_for_function("G.enemies.some(e => !e.dead && e.st && ((e.st.fire && e.st.fire.t > 0) || (e.st.poison && e.st.poison.t > 0)))", polling=100, timeout=8000)   # мобы Токио гибнут с удара — ждём, а не снимок в один момент
    assert js(page, "typeof drawElemIcons") == "function"


def _flash(page, loc, z):
    run(page, f"runCmd('unlock3'); travelTo({loc}); G.god = true; {ALL}")
    run(page, f"runCmd('tp {z}'); const b = makeBoss({z}); b.hp = b.maxHp = 1e15; b.x = hero.x + 150; b.y = hero.y; G.bosses[{z}] = b; G.enemies.push(b); toggleAuto(true);")
    run(page, "window.__fl = 0; setInterval(() => { if (G.flash > 0) window.__fl++; for (const e of G.enemies) if (e.boss && e.flash > 0) window.__fl++; }, 16);")
    page.wait_for_timeout(7000)
    return js(page, "window.__fl")


def test_flash_kurama(page):
    assert _flash(page, 2, 4) == 0


def test_flash_raiju(page):
    assert _flash(page, 3, 1) == 0


def _fps(browser, url, statuses):
    from conftest import _open
    ctx, p = _open(browser, url); cdp = ctx.new_cdp_session(p); cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
    p.evaluate("() => { runCmd('unlock3'); travelTo(3); runCmd('tower'); runCmd('twcp 61'); towerEnter(61, 1); runCmd('twfloor 67'); G.god = true; GFX.mode = 'mid'; GFX.level = 1; hero.x = 2000; hero.y = 1700; }")
    p.wait_for_timeout(4000)
    if statuses:
        p.evaluate("() => { window.__iv = setInterval(() => { for (const e of G.enemies) { if (e.dead) continue; applyElem(e, 'fire', 10, 'fire'); applyElem(e, 'poison', 10, 'poison', {dps: 1}); if (e.x & 1) applyElem(e, 'ice', 0, 'ice'); } }, 500); }")
    p.wait_for_timeout(1000)
    f = p.evaluate("() => new Promise(r => { let n = 0; const t0 = performance.now(); const k = () => { n++; if (performance.now() - t0 < 4000) requestAnimationFrame(k); else r(n / ((performance.now() - t0) / 1000)); }; requestAnimationFrame(k); })")
    ne = p.evaluate("() => G.enemies.filter(e => !e.dead).length")
    ctx.close(); return f, ne


@pytest.mark.slow
def test_fps_tower_statuses(browser, srv):
    med = lambda l: sorted(l)[1]
    a = [_fps(browser, srv, False) for _ in range(3)]; b = [_fps(browser, srv, True) for _ in range(3)]
    f0, f1 = med([x[0] for x in a]), med([x[0] for x in b])
    print('fps', f0, f1, 'enemies', [x[1] for x in b])
    assert f1 >= 0.9 * f0

from conftest import js, run, frames, load_save

FULL = "for (const s of SOUL) S.soul[s.id] = SOUL_MAX;"
COUNT = """() => { window.__c = {}; for (const n of ['drawStarAura', 'drawSakuraAura']) { const o = window[n]; window[n] = function (...a) { window.__c[n] = (window.__c[n] || 0) + 1; return o.apply(this, a); }; } }"""
SPY = """() => { window.__txt = []; window.__white = 0; const P = CanvasRenderingContext2D.prototype; if (window.__spy2) return; window.__spy2 = true;
  const f = P.fillText; P.fillText = function (t, ...a) { window.__txt.push(String(t)); return f.call(this, t, ...a); };
  const fr = P.fill, rect = P.fillRect; const chk = function () { const s = String(this.fillStyle).toLowerCase(); if (window.__inS && (s === '#ffffff' || s === '#fff' || s === 'white') && this.globalAlpha > 0.3) window.__white++; };
  P.fill = function (...a) { chk.call(this); return fr.apply(this, a); }; P.fillRect = function (...a) { chk.call(this); return rect.apply(this, a); };
  for (const n of ['drawStarAura', 'drawSakuraAura', 'drawStarOrb']) { const o = window[n]; window[n] = function (...a) { window.__inS = true; try { return o.apply(this, a); } finally { window.__inS = false; } }; } }"""


def setc(page, c):
    run(page, FULL + f" S.stars.peak = {c * 10}; refreshStats(); hero.x = 1500; hero.y = 1700;")


def test_aura_from_const1(page):
    page.evaluate(COUNT); setc(page, 0); frames(page, 10)
    assert js(page, "window.__c.drawStarAura || 0") == 0
    setc(page, 1); frames(page, 10)
    assert js(page, "window.__c.drawStarAura || 0") > 0


def test_trail_from_const3(page):
    setc(page, 2); run(page, "G.starTrail = []; hero.dashCd = 0; tryDash();"); frames(page, 3)
    assert js(page, "(G.starTrail || []).length") == 0
    setc(page, 3); run(page, "G.starTrail = []; hero.dashCd = 0; hero.dashT = 0; tryDash();"); frames(page, 3)
    assert js(page, "G.starTrail.length") > 0


def test_title_from_const5(page):
    page.evaluate(SPY); setc(page, 4); frames(page, 4)
    assert not any("Звёздная Аки" in t for t in js(page, "window.__txt"))
    setc(page, 5); run(page, "window.__txt = [];"); frames(page, 4)
    assert any("Звёздная Аки" in t for t in js(page, "window.__txt"))


def test_sakura_from_const10_all_looks(page):
    page.evaluate(COUNT); setc(page, 9); frames(page, 8)
    assert js(page, "window.__c.drawSakuraAura || 0") == 0
    for setup in ["", "runCmd('unlock'); travelTo(2);", "runCmd('unlock3'); travelTo(3);", "S.oni = true; refreshStats();"]:
        run(page, setup); setc(page, 10); run(page, "window.__c = {drawSakuraAura: 0};"); frames(page, 8)
        assert js(page, "window.__c.drawSakuraAura") > 0, setup


def test_no_white_and_slow(page):
    page.evaluate(SPY); setc(page, 10); run(page, "toggleSoul(true);"); page.wait_for_timeout(2500)
    run(page, "toggleSoul(false); hero.dashCd = 0; tryDash();"); page.wait_for_timeout(2500)
    assert js(page, "window.__white") == 0


def test_no_fx_in_tower(page, V6):
    load_save(page, V6); page.evaluate(COUNT)
    run(page, FULL + " S.stars.peak = 100; save(); towerEnter(1, 1);"); frames(page, 10)
    assert js(page, "(window.__c.drawStarAura || 0) + (window.__c.drawSakuraAura || 0)") == 0


def _fps(browser, url, setup):
    from conftest import _open
    ctx, p = _open(browser, url); cdp = ctx.new_cdp_session(p); cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
    p.evaluate(f"() => {{ GFX.mode = 'mid'; GFX.level = 1; {FULL} {setup} refreshStats(); hero.x = 640; hero.y = 1560; G.helpT = 0; }}"); p.wait_for_timeout(1500)
    f = p.evaluate("() => new Promise(r => { let n = 0; const t0 = performance.now(); const k = () => { n++; if (performance.now() - t0 < 4000) requestAnimationFrame(k); else r(n / ((performance.now() - t0) / 1000)); }; requestAnimationFrame(k); })")
    ctx.close(); return f


def test_fps_with_sakura(browser, srv):
    med = lambda l: sorted(l)[1]
    f0 = med([_fps(browser, srv, "S.stars.peak = 0;") for _ in range(3)])
    f1 = med([_fps(browser, srv, "S.stars.peak = 100;") for _ in range(3)])
    print('fps', f0, f1)
    assert f1 >= 0.9 * f0

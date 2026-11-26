from conftest import js, run, frames

SPY = """() => { window.__txt = []; window.__white = 0; const P = CanvasRenderingContext2D.prototype;
  if (!window.__spy) { window.__spy = true; const f = P.fillText; P.fillText = function (t, ...a) { if (window.__txt) window.__txt.push(String(t)); return f.call(this, t, ...a); };
    const fr = P.fill, rect = P.fillRect; const chk = function () { const s = String(this.fillStyle).toLowerCase(); if (window.__inV && (s === '#ffffff' || s === '#fff' || s === 'white') && this.globalAlpha > 0.3) window.__white++; };
    for (const n of ['drawVillagePlot', 'drawVillageGround', 'drawVillageLabels', 'vDecorExisting', 'drawVillageGoal', 'vDrawBossShard', 'drawShardLoot']) { const o = window[n]; window[n] = function (...a) { window.__inV = true; try { return o.apply(this, a); } finally { window.__inV = false; } }; }
    P.fill = function (...a) { chk.call(this); return fr.apply(this, a); }; P.fillRect = function (...a) { chk.call(this); return rect.apply(this, a); }; } }"""
NEW = ['ratusha', 'tea', 'spring', 'shrine', 'house1', 'house2', 'house3', 'house4', 'palisade', 'tower1', 'tower2']


def test_plots_inside_base_no_overlap(page):
    assert sorted(js(page, "Object.keys(VPLOTS)")) == sorted(NEW)
    bad = js(page, """Object.entries(VPLOTS).filter(([id, p]) => {
        if (p.x - p.w / 2 < 0 || p.x + p.w / 2 > baseW() || p.y - p.h < 0 || p.y > CFG.WORLD_H) return true;
        const hit = (o, r) => { const cx = clamp(o.x, p.x - p.w / 2, p.x + p.w / 2), cy = clamp(o.y, p.y - p.h, p.y); return Math.hypot(o.x - cx, o.y - cy) < r; };
        return [FORGE, BOARD, SHOP, NURSERY, PORTAL].some(o => hit(o, o.r + 30)) || hit(DUMMY, 70) || hit(SPAWN, 60) || (id !== 'ratusha' && hit(RATUSHA, RATUSHA.r + 20));
      }).map(([id]) => id)""")
    assert bad == []
    overlap = js(page, """(() => { const E = Object.entries(VPLOTS), r = []; for (let i = 0; i < E.length; i++) for (let j = i + 1; j < E.length; j++) { const a = E[i][1], b = E[j][1];
        if (Math.abs(a.x - b.x) < (a.w + b.w) / 2 && a.y - a.h < b.y && b.y - b.h < a.y) r.push(E[i][0] + '/' + E[j][0]); } return r; })()""")
    assert overlap == []


def test_sprite_cache_reused(page):
    run(page, "S.village.crystal = true; hero.x = 500; hero.y = 900;"); frames(page, 90)
    n1 = js(page, "VSPR.size"); frames(page, 20)
    assert js(page, "VSPR.size") == n1 and n1 > 0


def test_draw_no_errors_all_states(page):
    for loc in (1, 2, 3):
        for lv in (0, 1, 2, 3):
            run(page, f"runCmd('unlock3'); if (S.loc !== {loc}) travelTo({loc}); S.village.crystal = {str(lv > 0).lower()}; for (const b of VILLAGE) S.village.steps[b.id] = {lv}; S.village.queue = []; refreshStats();")
            for y in (700, 2700):
                run(page, f"hero.x = 500; hero.y = {y};"); frames(page, 4)
    run(page, "S.village.steps.tea = 1; S.village.steps.ratusha = 2; S.gold = 1e15; S.souls = 1e9; S.jade = 1e9; S.village.queue = []; vStartBuild('tea'); hero.x = 300; hero.y = 900;")
    frames(page, 10)


def test_no_white_fill(page):
    run(page, "S.village.crystal = true; for (const b of VILLAGE) S.village.steps[b.id] = 3; hero.x = 500; hero.y = 900;")
    page.evaluate(SPY); run(page, "VSPR.clear();"); page.wait_for_timeout(2500)
    run(page, "hero.x = 500; hero.y = 2700;"); page.wait_for_timeout(2500)
    run(page, "S.village.queue = [{ id: 'tea', step: 1, endTs: Date.now() + 9e5 }]; S.village.steps.tea = 0; hero.x = 300; hero.y = 900;"); page.wait_for_timeout(1500)
    assert js(page, "window.__white") == 0


def test_labels_text(page):
    run(page, "S.village.crystal = true; S.village.steps.ratusha = 1; S.village.steps.tea = 1; S.gold = 1e15; hero.x = 300; hero.y = 900;"); frames(page, 60)
    page.evaluate(SPY); frames(page, 4)
    t = js(page, "window.__txt")
    assert any("Чайный домик · шаг 1/3" in x for x in t)
    run(page, "vStartBuild('spring');"); page.evaluate(SPY); frames(page, 4)
    assert any(x.startswith("Горячий источник · строится ") for x in js(page, "window.__txt"))


def test_no_labels_without_crystal(page):
    run(page, "hero.x = 300; hero.y = 900;"); frames(page, 60); page.evaluate(SPY); frames(page, 4)
    assert not any("· шаг" in x for x in js(page, "window.__txt"))


def test_props_hidden_under_plots(page):
    assert js(page, "WORLD.trees.concat(WORLD.lamps || []).filter(o => vPlotAt(o.x, o.y) && !vPropHidden(o)).length") == 0


def _fps(browser, url, setup):
    from conftest import _open
    ctx, p = _open(browser, url)
    cdp = ctx.new_cdp_session(p); cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
    p.evaluate("() => { GFX.mode = 'mid'; GFX.level = 1; SET.gfx = 'mid'; }")
    p.evaluate(f"() => {{ {setup} hero.x = 500; hero.y = 1150; G.helpT = 0; }}"); p.wait_for_timeout(1500)
    f = p.evaluate("() => new Promise(r => { let n = 0; const t0 = performance.now(); const k = () => { n++; if (performance.now() - t0 < 4000) requestAnimationFrame(k); else r(n / ((performance.now() - t0) / 1000)); }; requestAnimationFrame(k); })")
    ctx.close(); return f


def test_fps_base_full_village(browser, srv, srv_orig):
    f0 = _fps(browser, srv_orig, "")
    f1 = _fps(browser, srv, "S.village.crystal = true; G.vDomeT = 2.5; for (const b of VILLAGE) S.village.steps[b.id] = 3; refreshStats();")
    print('fps v6', f0, 'village', f1)
    assert f1 >= 0.9 * f0

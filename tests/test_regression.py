from conftest import js, run, frames, load_save, travel

PICK = "() => { for (const l of G.loot) { l.x = hero.x; l.y = hero.y; l.t = 1; l.z = 0; } }"


def test_full_path_from_v6(page, V6):
    load_save(page, V6)
    page.wait_for_selector('#vl-say:not(.hidden)', timeout=4000)
    page.click('#vl-say [data-act="ok"]')
    run(page, "travelTo(1);"); frames(page, 5)
    for z in (1, 2, 3, 4):
        run(page, f"G.loot.length = 0; const b = makeBoss({z}); G.enemies.push(b); killEnemy(b);")
        page.evaluate(PICK); frames(page, 6)
    assert js(page, "S.village.crystal") is True
    page.wait_for_timeout(3000)
    run(page, "S.gold = 1e13; S.souls = 1e7; S.jade = 1e7;")
    assert js(page, "vStartBuild('ratusha')") is True
    travel(page, 3600e3); run(page, "vTick();")
    assert js(page, "vStep('ratusha')") == 1
    assert js(page, "[vStartBuild('tea')]") == [True]
    run(page, "save(); G.noSaveOnUnload = true;"); page.reload(); page.wait_for_function("typeof S==='object' && S.village", polling=100)
    assert js(page, "S.village.queue.length") == 1 and js(page, "vStep('ratusha')") == 1
    run(page, "S.village.steps.tower1 = 3; S.village.steps.house1 = 3; refreshStats();")
    hp_in = js(page, "ST.maxHp")
    run(page, "towerEnter(1, 1); refreshStats();")
    assert js(page, "vBonus('hp')") == 0
    run(page, "towerExit(); refreshStats();")
    assert js(page, "ST.maxHp") == hp_in and js(page, "vBonus('hp')") > 0
    run(page, "oniAwaken();"); frames(page, 5)
    assert js(page, "S.village.crystal") is True and js(page, "vStep('tower1')") == 3


def test_all_windows_smoke(page):
    run(page, "S.village.crystal = true; for (const b of VILLAGE) S.village.steps[b.id] = 2; refreshStats(); runCmd('unlock3');")
    for o, c in [("openForge()", "closeForge()"), ("openBoard()", "closeBoard()"), ("openShop()", "closeShop()"), ("openPets()", "closePets()"),
                 ("toggleTree(true)", "toggleTree(false)"), ("openTravel()", "closeTravel()"), ("toggleMenu(true)", "toggleMenu(false)"), ("openVillage()", "closeVillage()"), ("toggleSoul(true)", "toggleSoul(false)")]:
        run(page, o + ";"); frames(page, 4); run(page, c + ";"); frames(page, 2)


def _flash_fight(page, loc, z):
    run(page, f"runCmd('unlock3'); travelTo({loc}); G.god = true; S.village.crystal = true; for (const b of VILLAGE) S.village.steps[b.id] = 3; refreshStats();")
    run(page, f"runCmd('tp {z}'); const b = makeBoss({z}); b.hp = b.maxHp = 1e15; b.x = hero.x + 150; b.y = hero.y; G.bosses[{z}] = b; G.enemies.push(b); toggleAuto();")
    run(page, "window.__fl = 0; window.__iv = setInterval(() => { if (G.flash > 0) window.__fl++; for (const e of G.enemies) if (e.boss && e.flash > 0) window.__fl++; }, 16);")
    page.wait_for_timeout(8000)
    return js(page, "window.__fl")


def test_flash_kurama(page):
    assert _flash_fight(page, 2, 4) == 0


def test_flash_raiju(page):
    assert _flash_fight(page, 3, 1) == 0


def _forge_fps(browser, url):
    from conftest import _open
    ctx, p = _open(browser, url); cdp = ctx.new_cdp_session(p); cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
    p.evaluate("() => { GFX.mode = 'mid'; GFX.level = 1; document.body.classList.add('gfx-lo'); openForge(); }"); p.wait_for_timeout(1500)
    f = p.evaluate("() => new Promise(r => { let n = 0; const t0 = performance.now(); const k = () => { n++; if (performance.now() - t0 < 4000) requestAnimationFrame(k); else r(n / ((performance.now() - t0) / 1000)); }; requestAnimationFrame(k); })")
    ctx.close(); return f


def test_forge_fps_not_worse(browser, srv, srv_orig):
    med = lambda l: sorted(l)[1]
    f0 = med([_forge_fps(browser, srv_orig) for _ in range(3)])
    f1 = med([_forge_fps(browser, srv) for _ in range(3)])
    print('forge fps', f0, f1)
    assert f1 >= 0.9 * f0


def test_stars_full_path_from_v6(page, V6):
    load_save(page, V6)
    run(page, "for (const s of SOUL) S.soul[s.id] = SOUL_MAX; S.xp = 1e9; S.gold = 1e12; toggleSoul(true);")
    page.click('#soul [data-act="starmax"][data-id="pow"]')
    n = js(page, "S.stars.b.pow"); assert n >= 10 and js(page, "constN()") >= 1
    run(page, "toggleSoul(false); save(); G.noSaveOnUnload = true;"); page.reload(); page.wait_for_function("typeof S==='object' && S.stars", polling=100)
    assert js(page, "S.stars.b.pow") == n
    run(page, "openShop();"); page.click('#shop [data-act="starreset"]'); page.click('#shop [data-act="starreset"]')
    assert js(page, "starsTotal()") == 0 and js(page, "constN()") >= 1
    run(page, "closeShop(); towerEnter(1, 1);"); frames(page, 5); run(page, "towerExit(); oniAwaken();"); frames(page, 5)
    assert js(page, "constN()") >= 1


def test_elements_full_path_from_v6(page, V6):
    d = dict(V6); d.pop('elemMig', None)
    w = dict(d['w']); w['ench'] = [{'id': 'burn', 't': 5, 'v': 90}, None, None, None]; d['w'] = w
    a = dict(d['a']); a['ench'] = [{'id': 'thorns', 't': 4, 'v': 80}, None, None, None]; d['a'] = a
    load_save(page, d)
    assert js(page, "[S.w.ench[0].v, S.a.ench[0].id]") == [36, 'shell']
    run(page, "G.god = true; runCmd('tp 1'); toggleAuto(true);"); page.wait_for_timeout(2500)
    run(page, "toggleAuto(false); towerEnter(1, 1);"); frames(page, 10); run(page, "towerExit(); oniAwaken();"); frames(page, 10)
    assert js(page, "S.elemMig") == 2

"""Руны 2а, задача 8: полный путь со старого сейва v6 и безопасность вспышек с рунами."""
from conftest import js, run, frames, load_save

RUNESET = ("S.runes.w = [{id:'elem',r:5,f:[0,0,0,0,0,0]}, {id:'spirit',r:5,f:[0,0,0,0,0,0]}, {id:'shade',r:5,f:[0,0,0,0,0,0]}];"
           "S.runes.a = [{id:'heart',r:5,f:[0,0,0,0,0,0]}, {id:'time',r:5,f:[0,0,0,0,0,0]}, {id:'pierce',r:5,f:[0,0,0,0,0,0]}];"
           "S.ring.lvl = Math.max(1, S.ring.lvl); S.brace.lvl = Math.max(1, S.brace.lvl); S.neck.lvl = Math.max(1, S.neck.lvl);"
           "S.runes.j = [{id:'spirit',r:5,f:[0,0,0,0,0,0]}, {id:'shade',r:5,f:[0,0,0,0,0,0]}, {id:'heart',r:5,f:[0,0,0,0,0,0]}]; fixSlots(); refreshPetFx(); refreshStats();")


def test_full_path_from_v6(page, V6):
    load_save(page, V6)
    assert js(page, "S.runes.bag.length") == 0
    run(page, "runCmd('unlock3'); travelTo(3); fixSlots(); S.tower.charges = 2; G.god = true; towerEnter(1, 1); window.__mr = Math.random; Math.random = () => 0.001;")
    run(page, "for (let i = 0; i < 12; i++) { const e = makeTowerMob('bruiser', hero.x + 30, hero.y, false); G.enemies.push(e); killEnemy(e); } for (const l of G.loot) { l.x = hero.x; l.y = hero.y; l.t = 1; l.z = 0; l.vz = 0; }")
    run(page, "Math.random = window.__mr;")
    frames(page, 30)
    got = js(page, "S.runes.frag.reduce((a, b) => a + b, 0)")
    assert got >= 10
    run(page, "towerExit(false); S.runes.frag[0] = Math.max(10, S.runes.frag[0]); S.gold = 1e15; openForge(); G.forgeTab = 'r'; renderForge();")
    page.click("#forge [data-act='rforge'][data-slot='0']")
    page.click("#forge [data-act='rbag'][data-slot='0']")
    page.click("#forge [data-act='rins'][data-item='w'][data-slot='0']")
    rid = js(page, "S.runes.w[0].id")
    run(page, "closeForge(); save(); G.noSaveOnUnload = true;")
    page.reload()
    page.wait_for_function("typeof S==='object' && typeof hero==='object'", polling=100, timeout=15000)
    assert js(page, "S.runes.w[0].id") == rid and js(page, "runesOn()") is True


def test_dummy_shows_rune_sources(page):
    run(page, "runCmd('unlock3'); runCmd('soul 100'); S.tower.unlocked = true; travelTo(3); fixSlots(); S.w.rank = 12; refreshStats();" + RUNESET + "ST.critChance = 1;")
    r = js(page, "(() => { const d = G.dummy; G.enemies = [d]; d.hp = d.maxHp = 1e15; d.eva = 0; G.dsess = null; for (let i = 0; i < 12; i++) dealDamage(d, 10); runeShadeStep(d.x - 50, d.y, d.x + 50, d.y); return Object.keys(G.dsess.tot); })()")
    assert 'spirit' in r and 'shade' in r
    assert js(page, "DPS_SRC.spirit[0]") == 'Дух клинка' and js(page, "DPS_SRC.shade[0]") == 'Тень'


def _flash(page, loc, z):
    run(page, f"runCmd('unlock3'); runCmd('soul 100'); S.tower.unlocked = true; travelTo({loc}); G.god = true; {RUNESET}")
    run(page, f"runCmd('tp {z}'); const b = makeBoss({z}); b.hp = b.maxHp = 1e15; b.x = hero.x + 150; b.y = hero.y; G.bosses[{z}] = b; G.enemies.push(b); toggleAuto(true);")
    run(page, "window.__fl = 0; window.__dash = setInterval(() => { hero.dashCd = 0; tryDash({x: Math.random() < 0.5 ? 1 : -1, y: 0, mag: 1}); }, 700); setInterval(() => { if (G.flash > 0) window.__fl++; for (const e of G.enemies) if (e.boss && e.flash > 0) window.__fl++; }, 16);")
    page.wait_for_timeout(6000)
    return js(page, "window.__fl")


def test_flash_kurama_runes(page):
    assert _flash(page, 2, 4) == 0


def test_flash_raiju_runes(page):
    assert _flash(page, 3, 1) == 0


COMBOSET = ("S.ring.lvl = S.brace.lvl = S.neck.lvl = Math.max(1, S.ring.lvl);"
            "const _m = ids => ids.map(id => ({id, r: 5, f: [0,0,0,0,0,0]}));"
            "S.runes.w = _m(['elem', 'elem', 'elem']); S.runes.a = _m(['elem', 'elem', 'elem']); S.runes.j = _m(['spirit', 'shade', 'time']); refreshStats();")


def _flash_combo(page, loc, z):
    run(page, f"runCmd('unlock3'); runCmd('soul 100'); S.tower.unlocked = true; travelTo({loc}); G.god = true; {COMBOSET}")
    run(page, f"runCmd('tp {z}'); const b = makeBoss({z}); b.hp = b.maxHp = 1e15; b.x = hero.x + 150; b.y = hero.y; G.bosses[{z}] = b; G.enemies.push(b); toggleAuto(true);")
    run(page, "window.__fl = 0; setInterval(() => { hero.dashCd = 0; tryDash({x: Math.random() < 0.5 ? 1 : -1, y: 0, mag: 1}); }, 700); setInterval(() => { if (G.flash > 0) window.__fl++; for (const e of G.enemies) if (e.boss && e.flash > 0) window.__fl++; }, 16);")
    page.wait_for_timeout(6000)
    return js(page, "[window.__fl, ST.ru.rc.storm, ST.ru.rc.veil, ST.ru.rc.sakura]")


def test_flash_kurama_combos(page):
    assert _flash_combo(page, 2, 4) == [0, 5, 5, 5]


def test_flash_raiju_combos(page):
    assert _flash_combo(page, 3, 1) == [0, 5, 5, 5]

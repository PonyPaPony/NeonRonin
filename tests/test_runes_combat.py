"""Руны 2а, задача 4: «Дух Клинка», «Сердце Стража», «Пробой»."""
from conftest import js, run

BASE = "runCmd('unlock3'); runCmd('soul 100'); S.tower.unlocked = true; travelTo(3); fixSlots(); S.w.ench = [null, null, null, null]; refreshStats(); G.speed = 0.0001;"
R = "{id:'%s', r:%d, f:[0,0,0,0,0,0]}"
DUMMY = "const d = G.dummy; G.enemies = [d]; d.hp = d.maxHp = 1e15; d.eva = 0; d.def = 0; d.st = null; G.dsess = null;"
HIT = "(() => { const e = {x: hero.x + 30, y: hero.y%s}; hero.dead = false; hero.hp = 1e9; hero.shield = 0; hero.iframe = 0; hero.dashT = 0; damageHero(1000, e%s); return 1e9 - hero.hp; })()"


def test_spirit_katana(page):
    run(page, BASE + "Math.random = () => 0.5;")
    p0, c0 = js(page, "physMul({src:'katana'})"), js(page, "ST.critChance")
    run(page, f"S.runes.w[0] = {R % ('spirit', 5)}; refreshStats();")
    assert abs(js(page, "physMul({src:'katana'})") / p0 - 1.16) < 1e-9
    assert js(page, "physMul({src:'fire', el:'fire'})") == 1
    assert abs(js(page, "ST.critChance") - (c0 + 0.04)) < 1e-9


def test_spirit_armor_phys_only(page):
    run(page, BASE + "Math.random = () => 0.99;")
    a, ae = js(page, HIT % ('', '')), js(page, HIT % ('', ", 'fire'"))
    run(page, f"S.runes.a[0] = {R % ('spirit', 5)}; refreshStats();")
    b, be = js(page, HIT % ('', '')), js(page, HIT % ('', ", 'fire'"))
    assert abs(b / a - 0.88) < 1e-6 and abs(be / ae - 1) < 1e-6


def test_spirit_burst_10_phys_crits(page):
    run(page, BASE + f"S.brace.lvl = 1; S.runes.j[1] = {R % ('spirit', 5)}; refreshStats(); ST.critChance = 1;")
    r = js(page, "(() => { " + DUMMY + " for (let i = 0; i < 9; i++) dealDamage(d, 10); const a = (G.dsess && G.dsess.tot.spirit) || 0; dealDamage(d, 10); return [a, G.dsess.tot.spirit || 0, ST.dmg, d.st.mk.n]; })()")
    assert r[0] == 0 and r[3] == 0
    assert abs(r[1] / (4 * r[2]) - 1) < 0.12                     # 400% урона героини (до множителей; защита 0, «Острота» нет)
    r = js(page, "(() => { " + DUMMY + " for (let i = 0; i < 5; i++) dealDamage(d, 10, {src:'chain', el:'thunder', noProc:true}); elemDmg(d, 'fire', 10, 'fire', true); return (d.st && d.st.mk && d.st.mk.n) || 0; })()")
    assert r == 0                                                 # молнии и горение меток не кладут
    r = js(page, "(() => { " + DUMMY + " for (let i = 0; i < 3; i++) dealDamage(d, 10); G.time += 4.1; dealDamage(d, 10); return d.st.mk.n; })()")
    assert r == 1                                                 # 4 с без крита — метки сгорели


def test_heart_katana_dmg_and_shield(page):
    run(page, BASE + "Math.random = () => 0.5; hero.shield = 0;")
    r = js(page, "(() => { " + DUMMY + " hero.x = d.x - 40; hero.y = d.y; hero.swingCount = 0; heroAttack(d); return G.dsess.tot.katana; })()")
    run(page, f"S.runes.w[0] = {R % ('heart', 5)}; refreshStats(); hero.shield = 0;")
    r2 = js(page, "(() => { " + DUMMY + " hero.x = d.x - 40; hero.y = d.y; hero.swingCount = 0; heroAttack(d); return [G.dsess.tot.katana, hero.shield, ST.maxHp, ST.dmg]; })()")
    assert abs((r2[0] - r) - r2[2] * 0.01) / (r2[2] * 0.01) < 0.12   # +1% макс. HP к удару
    assert 0 < r2[1] <= r2[2] * 0.01 + 1e-6                          # щит за удар ≤ 1% макс. HP
    cap = js(page, "(() => { " + DUMMY + " for (let i = 0; i < 200; i++) dealDamage(d, ST.maxHp); return [hero.shield, ST.maxHp]; })()")
    assert abs(cap[0] - cap[1] * 0.2) < 1e-6                         # предел 20% макс. HP


def test_heart_armor_hp(page):
    run(page, BASE)
    h0 = js(page, "ST.maxHp")
    run(page, f"S.runes.a[2] = {R % ('heart', 5)}; refreshStats();")
    assert abs(js(page, "ST.maxHp") / h0 - 1.2) < 1e-9


def test_second_breath(page):
    run(page, BASE + f"S.neck.lvl = 1; S.runes.j[2] = {R % ('heart', 5)}; refreshStats(); Math.random = () => 0.99; G.breathCd = 0;")
    r = js(page, "(() => { hero.dead = false; hero.hp = ST.maxHp * 0.35; hero.shield = 0; hero.iframe = 0; const m = ST.maxHp; hero.hp = m * 0.31; damageHero(m * 0.02); return [hero.hp / m, hero.shield / m, G.breathCd - G.time]; })()")
    assert r[0] > 0.6 and abs(r[1] - 0.25) < 1e-6 and r[2] > 59
    r = js(page, "(() => { const m = ST.maxHp; hero.hp = m * 0.31; hero.shield = 0; hero.iframe = 0; damageHero(m * 0.02); return [hero.hp / m, hero.shield / m]; })()")
    assert r[0] < 0.31 and r[1] == 0                                 # откат 60 с


def test_pierce_crack(page):
    run(page, BASE + f"S.runes.w[0] = {R % ('pierce', 5)}; refreshStats(); Math.random = () => 0.5;")
    r = js(page, "(() => { " + DUMMY + " d.def = 0.4; for (let i = 0; i < 10; i++) dealDamage(d, 1); const red = runeCrack(d); G.dsess = null; dealDamage(d, 1000); const hit = G.dsess.tot.katana; const n = d.st.cr.n; return [red, hit, n]; })()")
    assert abs(r[0] - 0.6) < 1e-9
    fresh = js(page, "(() => { const d = G.dummy; d.def = 0.4; d.st = null; G.dsess = null; S.runes.w[0] = null; refreshStats(); dealDamage(d, 1000); return G.dsess.tot.katana; })()")
    assert abs(r[1] / fresh - (1 - 0.16) / (1 - 0.4)) < 1e-6
    run(page, f"S.runes.w[0] = {R % ('pierce', 5)}; refreshStats();")
    r = js(page, "(() => { const d = G.dummy; d.st = null; for (let i = 0; i < 10; i++) dealDamage(d, 1); const n0 = d.st.cr.n; G.time += 3 + 1.5 * 2 + 0.1; return [runeCrack(d), n0]; })()")
    assert r[1] == 8                                                  # стаков не больше, чем нужно до предела 60%
    assert abs(r[0] - 0.4) < 1e-9                                     # 8 → 5 стаков (−8% за стак)
    r = js(page, "(() => { const d = G.dummy; d.st = null; dealDamage(d, 1, {src:'pet', small:true, noProc:true}); return runeCrack(d); })()")
    assert r == 0                                                     # питомец «Раскол» не кладёт


def test_pierce_armor_frail(page):
    run(page, BASE)
    assert abs(js(page, f"(() => {{ S.curses.frail = 3; S.runes.a[0] = {R % ('pierce', 5)}; refreshStats(); return ST.frail; }})()") - (1 + 0.45 * 0.4)) < 1e-9


def test_icons_marks_visible_only(page):
    run(page, BASE + f"S.brace.lvl = 1; S.runes.j[1] = {R % ('spirit', 5)}; S.runes.w[0] = {R % ('pierce', 5)}; refreshStats(); ST.critChance = 1;")
    r = js(page, """(() => { const d = G.dummy; d.st = null; d.hp = d.maxHp = 1e15; d.eva = 0; for (let i = 0; i < 3; i++) dealDamage(d, 1);
      const c = document.createElement('canvas').getContext('2d'), txt = []; const f = c.fillText.bind(c); c.fillText = (s, ...a) => { txt.push(String(s)); f(s, ...a); };
      drawElemIcons(c, d); return txt; })()""")
    assert any('3' in t for t in r)                                    # счётчик меток / Раскола у врага

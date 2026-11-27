"""Руны 2а, задача 5: «Тень» (Теневой шаг, крит после уклонения, уклонение после крита) и «Время»."""
from conftest import js, run

BASE = "runCmd('unlock3'); runCmd('soul 100'); S.tower.unlocked = true; travelTo(3); fixSlots(); S.w.rank = 12; S.w.ench = [null, null, null, null]; refreshStats(); G.speed = 0.0001;"
R = "{id:'%s', r:%d, f:[0,0,0,0,0,0]}"
MOBS = """const mk = (dx, dy) => { const e = makeEnemy('bruiser', hero.x + dx, hero.y + dy, 1, false); e.hp = e.maxHp = 1e15; e.eva = 0; e.def = 0; G.enemies.push(e); return e; };
  G.enemies.length = 0; G.dsess = null; const L = [mk(60, 0), mk(120, 10), mk(180, -10), mk(120, 130)];"""


def test_shadow_step_hits_path(page):
    run(page, BASE + f"S.runes.w[0] = {R % ('shade', 5)}; refreshStats(); hero.dashCd = 0; ST.critChance = 0;")
    r = js(page, "(() => { " + MOBS + """ const hp = () => L.map(e => e.hp < 1e15);
      tryDash({x: 1, y: 0, mag: 1}); runeShadeStep(hero.x, hero.y, hero.x + 200, hero.y); const a = hp(); const v1 = L.map(e => e.hp);
      runeShadeStep(hero.x, hero.y, hero.x + 200, hero.y); const same = L.every((e, i) => e.hp === v1[i]);
      hero.dashCd = 0; tryDash({x: 1, y: 0, mag: 1}); runeShadeStep(hero.x, hero.y, hero.x + 200, hero.y); const again = L[0].hp < v1[0];
      return [a, same, again]; })()""")
    assert r[0] == [True, True, True, False] and r[1] is True and r[2] is True


def test_shadow_step_damage_value(page):
    run(page, BASE + f"S.runes.w[0] = {R % ('shade', 5)}; refreshStats(); Math.random = () => 0.5;")
    r = js(page, "(() => { " + MOBS + " tryDash({x: 1, y: 0, mag: 1}); runeShadeStep(hero.x, hero.y, hero.x + 70, hero.y); return [1e15 - L[0].hp, ST.dmg * ST.skillMul]; })()")
    assert abs(r[0] / (2 * r[1]) - 1) < 0.01                          # 200% урона героини × сила способностей (как вихрь и волна)


def test_shade_armor_crit_after_dodge(page):
    run(page, BASE + f"S.runes.a[0] = {R % ('shade', 5)}; refreshStats(); ST.critChance = 0; Math.random = () => 0.5;")
    r = js(page, """(() => { const d = G.dummy; G.enemies = [d]; d.hp = d.maxHp = 1e15; d.eva = 0; d.def = 0; hero.dead = false; hero.hp = 1e9; hero.iframe = 0; hero.dashT = 0;
      ST.dodge = 0.3; Math.random = () => 0; damageHero(100, d); Math.random = () => 0.5; const h = []; const sp = spawnText; spawnText = (x, y, t, c, s, crit) => { if (crit) h.push(t); };
      dealDamage(d, 10); const a = h.length; dealDamage(d, 10); const b = h.length; hero.iframe = 0; ST.dodge = 0.3; Math.random = () => 0; damageHero(100, d); Math.random = () => 0.5; dealDamage(d, 10); const c = h.length; spawnText = sp; return [a, b, c]; })()""")
    assert r == [1, 1, 1]                                              # первый удар после уклона — крит, второй — нет; повтор раньше отката (3 с) — нет


def test_shade_jewel_dodge_buff(page):
    run(page, BASE + f"S.brace.lvl = 1; S.runes.j[1] = {R % ('shade', 5)}; refreshStats(); ST.critChance = 1;")
    r = js(page, "(() => { const d = G.dummy; d.eva = 0; d.hp = d.maxHp = 1e15; const a = runeDodge(); dealDamage(d, 10); const b = runeDodge(); ST.dodge = 0.4; const c = runeDodge(); G.time += 2.1; const e = runeDodge(); return [a, b, c, e]; })()")
    assert abs(r[1] - (r[0] + 0.12)) < 1e-9 and r[2] == 0.45 and r[3] == 0.4


def test_time_whirl_chance(page):
    run(page, BASE + f"S.runes.w[1] = {R % ('time', 5)}; refreshStats(); Math.random = () => 0;")
    r = js(page, "(() => { const d = G.dummy; G.enemies = [d]; d.hp = d.maxHp = 1e15; d.eva = 0; G.dsess = null; hero.x = d.x - 40; hero.y = d.y; hero.swingCount = 0; heroAttack(d); return !!(G.dsess && G.dsess.tot.whirl > 0); })()")
    assert r is True
    run(page, "Math.random = () => 0.99;")
    r = js(page, "(() => { const d = G.dummy; d.hp = d.maxHp = 1e15; G.dsess = null; hero.swingCount = 0; heroAttack(d); return !!(G.dsess && G.dsess.tot.whirl > 0); })()")
    assert r is False


def test_time_dash_cd(page):
    run(page, BASE)
    a = js(page, "ST.dashCd")
    run(page, f"S.runes.a[1] = {R % ('time', 5)}; refreshStats();")
    assert abs(js(page, "ST.dashCd") / a - 0.8) < 1e-9


def test_time_jewel_oni(page):
    run(page, BASE + "S.neck.lvl = 1; S.oni = true; S.pets.active = null; refreshPetFx(); refreshStats(); G.oniSuperT = 0;")
    a = js(page, "(() => { S.oniE = 0; gainOniEnergy(1); return S.oniE; })()")
    run(page, f"S.runes.j[2] = {R % ('time', 5)}; refreshStats();")
    b = js(page, "(() => { S.oniE = 0; gainOniEnergy(1); return S.oniE; })()")
    assert abs(b / a - 1.32) < 1e-9
    assert js(page, "(() => { S.oniE = 100; S.oniCd = 0; G.oniSuperT = 0; tryOniSuper(); return S.oniCd; })()") == 288


def test_time_jewel_pet_ult(page):
    run(page, BASE + f"S.neck.lvl = 1; S.runes.j[2] = {R % ('time', 5)}; refreshStats();")
    assert js(page, "runePetCd('firestorm')") == 36
    run(page, "S.oni = true; refreshStats();")
    assert js(page, "runePetCd('firestorm')") == 45                   # у Они «Время» ускоряет Ярость, а не ульту


def test_afterimage_no_white(page):
    run(page, BASE + f"S.runes.w[0] = {R % ('shade', 5)}; refreshStats();")
    r = js(page, "(() => { GFX.level = 2; G.particles.length = 0; tryDash({x: 1, y: 0, mag: 1}); for (let i = 0; i < 6; i++) runeShadeStep(hero.x + i * 10, hero.y, hero.x + i * 10 + 10, hero.y); return G.particles.filter(p => p.shade).map(p => p.color); })()")
    assert 0 < len(r) <= 3 and all('255,255,255' not in c for c in r)

"""Этап 3: питомец Тётин — бумажный фонарик-призрак, свет фонаря, ветки и ульты."""
from conftest import js, run

BASE = ("runCmd('открыть всё'); runCmd('soul 100'); travelTo(3); fixSlots(); S.tower.unlocked = true; refreshStats(); G.speed = 0.0001;"
        "window.own = (lvl, picks) => { S.pets.owned.chochin = {lvl, xp: 0, picks: picks || [], x2: []}; S.pets.active = 'chochin'; spawnPetEntity(); refreshPetFx(); refreshStats(); };"
        "hero.x = 3000; hero.y = 1700; hero.face = 1;")
MOBS = ("const mk = (dx, dy) => { const e = makeEnemy('bruiser', hero.x + dx, hero.y + dy, 1, false); e.hp = e.maxHp = 1e15; e.eva = 0; e.def = 0; G.enemies.push(e); return e; };"
        "G.enemies.length = 0; Math.random = () => 0.5; ST.critChance = 0;")


# ---------- Task 1 ----------
def test_chochin_data(page):
    r = js(page, "[!!PET_SP.chochin, PET_SP.chochin && PET_SP.chochin.forms.length, PET_TREE.chochin && PET_TREE.chochin.length, PET_TREE.chochin && PET_TREE.chochin.every(t => t.length === 2),"
                 " PET_TREE.chochin && PET_TREE.chochin[5].map(o => o.fx.ult), TOWER_PETS.chochin, PET_ORDER.includes('chochin')]")
    assert r == [True, 3, 6, True, ['liberate', 'souls'], 1, True]
    run(page, BASE)
    assert js(page, "(() => { const s = new Set(); for (let i = 0; i < 300; i++) for (const z of [1, 2, 3, 4]) s.add(eggFor(z)); return s.has('chochin'); })()") is False   # в Питомнике яйцо Тётина не выпадает


def test_chochin_stays_close(page):
    run(page, BASE + "own(20);")
    r = js(page, "(() => { G.loot.length = 0; dropLoot('gold', hero.x + 250, hero.y, 1); for (const l of G.loot) { l.t = 1; l.vx = l.vy = l.vz = 0; l.z = 0; } for (let i = 0; i < 200; i++) updatePet(0.016); return [dist(G.pet.x, G.pet.y, hero.x, hero.y), !!G.pet.target]; })()")
    assert r[0] <= 70 and r[1] is False                                # держится у плеча, за лутом не бегает


def test_chochin_loot_magnet(page):
    run(page, BASE + "own(20);")
    r = js(page, "(() => { for (let i = 0; i < 60; i++) updatePet(0.016); G.loot.length = 0; dropLoot('gold', G.pet.x + 90, G.pet.y, 1); dropLoot('gold', G.pet.x + 170, G.pet.y, 1); for (const l of G.loot) { l.t = 1; l.vx = l.vy = l.vz = 0; l.z = 0; } updatePet(0.016); return G.loot.map(l => !!l.attract); })()")
    assert r == [True, False]                                          # лут в радиусе 110 сам летит к Тётину


def test_chochin_light(page):
    run(page, BASE + "own(20);")
    r = js(page, "(() => { for (let i = 0; i < 60; i++) updatePet(0.016); const L = chochinLight(); return [L && L.r, inLight(G.pet.x + 150, G.pet.y), inLight(G.pet.x + 220, G.pet.y)]; })()")
    assert r == [180, True, False]
    run(page, "S.pets.owned.cat = {lvl: 20, xp: 0, picks: [], x2: []}; S.pets.active = 'cat'; spawnPetEntity();")
    assert js(page, "[chochinLight(), inLight(hero.x, hero.y)]") == [None, False]


def test_chochin_in_tower_keeps_bonuses(page):
    run(page, BASE + "own(50, [1, 1, 1, 1, 1, 1]);")
    assert js(page, "PFX.lightDmg") == 0.1
    run(page, "S.loc = 4; refreshPetFx();")
    r = js(page, "[PFX.lightDmg, PFX.ult]")
    run(page, "S.loc = 3; refreshPetFx();")
    assert r == [0.1, 'souls']                                         # в Башне — с бонусами (он оттуда родом)


def test_old_save_pets_ok(page):
    run(page, BASE + "S.pets.owned.chochin = {lvl: 99, xp: -5, picks: [0, 1, 7]}; fixPets();")
    assert js(page, "[S.pets.owned.chochin.lvl, S.pets.owned.chochin.picks.join(',')]") == [50, '0,1,']


# ---------- Task 2 ----------
def test_light_dmg_and_crit(page):
    run(page, BASE + "own(50, [1, 1, 1, 1, 1, 1]);")
    r = js(page, "(() => { for (let i = 0; i < 60; i++) updatePet(0.016); " + MOBS + " const a = mk(60, 0), b = mk(600, 0);"
                 " dealDamage(a, 1000, {noKb: true, noProc: true}); dealDamage(b, 1000, {noKb: true, noProc: true}); const da = 1e15 - a.hp, db = 1e15 - b.hp;"
                 " a.hp = b.hp = 1e15; ST.critChance = 1; dealDamage(a, 1000, {noKb: true, noProc: true}); dealDamage(b, 1000, {noKb: true, noProc: true});"
                 " return [da / db, (1e15 - a.hp) / (1e15 - b.hp), ST.critDmg]; })()")
    assert abs(r[0] - 1.1) < 1e-6                                      # «Ночная охота» +10%
    assert abs(r[1] - 1.1 * (r[2] + 0.25) / r[2]) < 1e-6               # «Ясный свет» +25% крит. урона


def test_elite_mark(page):
    run(page, BASE + "own(50, [1, 0, 0, 0, 0, 0]);")
    r = js(page, "(() => { " + MOBS + " const a = mk(600, 0), b = mk(640, 0); a.elite = true; dealDamage(a, 1000, {noKb: true, noProc: true}); dealDamage(b, 1000, {noKb: true, noProc: true}); return (1e15 - a.hp) / (1e15 - b.hp); })()")
    assert abs(r - 1.15) < 1e-6


def test_light_regen_oni_too(page):
    run(page, BASE + "S.oni = true; own(50, [1, 1, 1, 1, 1, 1]);")
    r = js(page, "(() => { hero.hp = ST.maxHp * 0.5; const h = hero.hp; for (let i = 0; i < 60; i++) updatePet(1 / 60); return (hero.hp - h) / ST.maxHp; })()")
    assert abs(r - 0.005) < 0.0006                                     # 0,5% HP за секунду


def test_spirit_shield(page):
    run(page, BASE + "own(50, [1, 1, 1, 1, 1, 1]);")
    r = js(page, "(() => { hero.shield = 0; G.pet.spT = 0; updatePet(0.016); const a = hero.shield / ST.maxHp; updatePet(0.016); return [a, hero.shield / ST.maxHp, G.pet.spT > 7]; })()")
    assert abs(r[0] - 0.05) < 1e-6 and abs(r[1] - 0.05) < 1e-6 and r[2] is True   # раз в 8 с


def test_chochin_branch_a_tower_only(page):
    run(page, BASE + "own(50, [0, 0, 0, 0, 0, 0]);")
    r = js(page, "(() => { const f = {e: {elite: false}}; let n = 0; Math.random = () => 0.017; const e = {x: hero.x, y: hero.y}; G.loot.length = 0; runeFragDrop(e); n = G.loot.length;"
                 " const b = {x: hero.x, y: hero.y, boss: true}; G.loot.length = 0; runeFragDrop(b); return [n, G.loot.length]; })()")
    assert r == [1, 7]                                                 # +25% шанса (1,5% → 1,875%) и +2 с босса
    run(page, "travelTo(3); refreshPetFx();")
    assert js(page, "(() => { const t0 = Date.now(); S.tower.charges = 2; S.tower.run = null; towerEnter(1, 1); const left = S.tower.run.endTs - t0; towerExit && towerExit(); return Math.round(left / 1000); })()") >= 30 * 60 + 150 - 2


def test_frag_up_and_fly(page):
    run(page, BASE + "own(50, [0, 0, 0, 0, 0, 0]); S.tower.kills = 30 * 10000;")
    r = js(page, "(() => { const tw = G.tw, run = S.tower.run; G.tw = {floor: 15}; S.tower.run = {lvl: 3, mods: []}; Math.random = () => 0.05; G.loot.length = 0; runeFragDrop({x: hero.x, y: hero.y, boss: true}); G.tw = tw; S.tower.run = run; return G.loot.map(l => l.val); })()")
    assert all(v == 2 for v in r)                                      # этаж 15 — необычный (1), «Светлое чутьё» → редкий (2)
    r = js(page, "(() => { for (let i = 0; i < 60; i++) updatePet(0.016); G.loot.length = 0; dropLoot('rfrag', G.pet.x + 600, G.pet.y, 1); for (const l of G.loot) { l.t = 1; l.vx = l.vy = l.vz = 0; l.z = 0; } const L = S.loc; S.loc = 4; updatePet(0.016); S.loc = L; return G.loot[0].attract; })()")
    assert r is True                                                   # фрагменты летят к Тётину издалека


def test_souls_counter_cap_and_reset(page):
    run(page, BASE + "own(50, [1, 1, 1, 1, 1, 1]); S.tower.kills = 11 * 10000;")
    r = js(page, "(() => { G.chSouls = 0; G.chKills = 0; for (let i = 0; i < 25 * 50; i++) chochinKill(); const cap = G.chSouls; " + MOBS +
                 " for (let i = 0; i < 60; i++) updatePet(0.016); const b = mk(60, 0), c = mk(70, 0); b.boss = true; dealDamage(b, 1000, {noKb: true, noProc: true}); dealDamage(c, 1000, {noKb: true, noProc: true});"
                 " const k = (1e15 - b.hp) / (1e15 - c.hp); G.enemies.length = 0; hero.hp = 0; heroDie(); return [cap, k, G.chSouls]; })()")
    assert r[0] == 42 and abs(r[1] - 1.42) < 1e-6 and r[2] == 0         # потолок 30 + 12, +1% за душу по боссам в свете, сброс при смерти
    run(page, "hero.dead = false; hero.hp = ST.maxHp; S.tower.kills = 80 * 10000; G.chSouls = 0; G.chKills = 0; for (let i = 0; i < 25 * 80; i++) chochinKill();")
    assert js(page, "G.chSouls") == 60
    run(page, "travelTo(2);")
    assert js(page, "G.chSouls") == 0


def test_liberate_hits(page):
    run(page, BASE + "own(50, [0, 0, 0, 0, 0, 0]);")
    r = js(page, "(() => { " + MOBS + " const a = mk(100, 0), b = mk(-100, 40); G.pet.ultT = 0; updatePet(0.016); return [a.hp < 1e15, b.hp < 1e15, G.pet.ultT > 40]; })()")
    assert r == [True, True, True]

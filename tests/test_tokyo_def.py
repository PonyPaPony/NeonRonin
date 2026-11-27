"""Этап 2в: защита Токио/Храма (здоровье с поправкой) и мелочи из 2б."""
from conftest import js, run
from test_runes_combos import BASE


def test_tokyo_def_neutral_per_hit(page):
    run(page, "runCmd('unlock'); runCmd('rank_weapon 8'); runCmd('loc 2'); fixSlots(); refreshStats(); ST.pen = 0;")
    r = js(page, "(() => { Math.random = () => 0.5; ST.critChance = 0; const e = makeEnemyRaw('bruiser', 3000, 1700, 4, false); e.eva = 0; G.enemies.push(e); const h0 = e.hp; dealDamage(e, 1000, {noKb: true, noProc: true}); return (h0 - e.hp) / h0 * ENEMY_TYPES.bruiser.hp * ZONES[4].hpM / (1000 * physMul({})); })()")
    assert abs(r - 1) < 1e-6                                          # доля здоровья за удар — как без защиты


def test_tokyo_def_values(page):
    assert js(page, "ZONES1.slice(1).map(z => z.def)") == [0.02, 0.04, 0.06, 0.08]
    assert js(page, "ZONES2.slice(1).map(z => z.def)") == [0.10, 0.12, 0.14, 0.16]


def test_tokyo_def_neutral(page):
    run(page, "runCmd('открыть всё'); travelTo(1);")
    r = js(page, "(() => { const e = makeEnemyRaw('bruiser', 3000, 1700, 4, false), b = makeBossRaw(4); return [e.hp / (1 - e.def) / (ENEMY_TYPES.bruiser.hp * ZONES[4].hpM), b.hp / (1 - b.def) / (1000 * ZONES[4].hpM * (ZONES[4].boss.hpX || 1)), e.def, b.def]; })()")
    assert abs(r[0] - 1) < 1e-9 and abs(r[1] - 1) < 1e-9 and r[2] == 0.08 and abs(r[3] - 0.064) < 1e-9
    run(page, "travelTo(2);")
    r = js(page, "(() => { const e = makeEnemyRaw('bruiser', 3000, 1700, 1, false); return [e.def, e.hp / (1 - e.def) / (ENEMY_TYPES.bruiser.hp * ZONES[1].hpM)]; })()")
    assert r[0] == 0.1 and abs(r[1] - 1) < 1e-9
    run(page, "travelTo(3);")
    r = js(page, "(() => { const e = makeEnemyRaw('bruiser', 3000, 1700, 1, false); return e.hp / (ENEMY_TYPES.bruiser.hp * ZONES[1].hpM); })()")
    assert abs(r - 1) < 1e-9                                          # в горах — без поправки (защита там была и раньше)


def test_tower_def_comp(page):
    run(page, "runCmd('открыть всё'); S.tower.run = S.tower.run || {lvl: 1, mods: []}; S.tower.run.lvl = 1; S.tower.run.mods = [];")
    r = js(page, "(() => { const Z = towerZoneStats(1); return [Z.def, Z.hpM / (1 - Z.def), Z12[0].hpM]; })()")
    assert abs(r[0] - 0.01) < 1e-9 and abs(r[1] - r[2]) < 1e-6 * r[2]


def test_hint_wrong_slot_text(page):
    run(page, BASE + "put('w', ['elem', 'spirit', 'elem']);")
    h = js(page, "runeComboHints('w').join(' | ')")
    assert 'До «Явление Кирина» не хватает: Пробой' in h and 'Стихия должна стоять в громовом' in h and 'Стихия (гром)' not in h


def test_hints_off_when_runes_off(page):
    run(page, BASE + "put('w', ['spirit', 'elem', 'pierce']); S.mainStash = {};")
    assert js(page, "runeComboHints('w').length") == 0
    run(page, "S.mainStash = null;")


def test_pack_clamped(page):
    run(page, BASE + "S.pets.owned.cat = {lvl: 20, xp: 0, picks: []}; S.pets.active = 'cat'; spawnPetEntity(); put('w', ['bond', 'shade', 'time']);")
    r = js(page, "(() => { G.pet.x = CFG.WORLD_W - 50; G.pet.y = 1700; runePack(1, 0); const a = G.pet.x; G.pet.x = baseW() + 60; hero.x = baseW() + 200; runePack(-1, 0); return [a <= CFG.WORLD_W - 20, G.pet.x >= baseW()]; })()")
    assert r == [True, True]

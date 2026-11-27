"""Руны 2а, задача 3: руны «Стихия» (стихия по слоту) и «Яд» в катане, доспехе и бижутерии."""
from conftest import js, run

BASE = "runCmd('unlock3'); S.tower.unlocked = true; travelTo(3); fixSlots(); S.w.ench = [null, null, null, null]; refreshStats(); G.speed = 0.0001;"
R = "{id:'%s', r:%d, f:[0,0,0,0,0,0]}"
DUMMY = "const d = G.dummy; G.enemies = [d]; d.hp = d.maxHp = 1e15; d.eva = 0; d.def = 0; d.st = null; G.dsess = null;"


def test_elem_rune_by_slot(page):
    run(page, BASE)
    assert js(page, "ST.elV.fire") == 0
    run(page, f"S.runes.w[0] = {R % ('elem', 5)}; refreshStats();")
    assert abs(js(page, "ST.elV.fire") - 0.24) < 1e-9 and js(page, "ST.elV.ice") == 0
    run(page, f"S.runes.w[0] = null; S.runes.w[2] = {R % ('elem', 5)}; refreshStats();")
    assert abs(js(page, "ST.elV.ice") - 0.20) < 1e-9 and js(page, "ST.elV.fire") == 0


def test_elem_rune_adds_to_enchant(page):
    run(page, BASE + f"S.w.ench[0] = {{id:'burn', t:4, v:24}}; S.runes.w[0] = {R % ('elem', 5)}; refreshStats();")
    assert abs(js(page, "ST.elV.fire") - 0.48) < 1e-9


def test_thunder_rune_zap_and_bolt(page):
    run(page, BASE + f"S.runes.w[1] = {R % ('elem', 5)}; refreshStats();")
    assert abs(js(page, "ST.ru.zapChance") - 0.16) < 1e-9
    r = js(page, "(() => { " + DUMMY + " Math.random = () => 0; dealDamage(d, 100); return [d.st && d.st.zap && d.st.zap.t, !!(G.dsess && G.dsess.tot.chain > 0)]; })()")
    assert abs(r[0] - 2) < 0.05 and r[1] is True
    r = js(page, "(() => { " + DUMMY + " Math.random = () => 0.99; dealDamage(d, 100); return [d.st && d.st.zap && d.st.zap.t, !!(G.dsess && G.dsess.tot.chain > 0)]; })()")
    assert abs(r[0] - 2) < 0.05 and r[1] is False                  # заряд — всегда, молния — по шансу


def test_elem_armor_res_and_immunity(page):
    run(page, BASE)
    f0, c0 = js(page, "ST.res.fire"), js(page, "ST.cdr")
    imm = js(page, f"(() => {{ S.runes.a = [{R % ('elem', 5)}, {R % ('elem', 5)}, {R % ('elem', 5)}]; refreshStats(); hero.hburn = null; hero.slowT = 0; applyElemEffect('fire', 100); applyElemEffect('ice', 100); return [hero.hburn, hero.slowT || 0]; }})()")
    assert abs(js(page, "ST.res.fire") - (f0 + 0.16)) < 1e-9
    assert imm == [None, 0]
    assert abs(js(page, "ST.cdr") - (c0 + 0.04)) < 1e-9
    assert js(page, "(() => { S.runes.a = [null, null, null]; refreshStats(); hero.hburn = null; applyElemEffect('fire', 100); return !!hero.hburn; })()") is True


def test_elem_jewel_duration(page):
    run(page, BASE + f"S.ring.lvl = 1; S.w.ench[0] = {{id:'burn', t:4, v:24}}; S.runes.j[0] = {R % ('elem', 5)}; refreshStats();")
    t = js(page, "(() => { " + DUMMY + " applyElem(d, 'fire', 100, 'fire'); return d.st.fire.t; })()")
    assert abs(t - 4.2) < 0.05
    run(page, "S.ring.lvl = 0; refreshStats();")                    # украшения нет — руна спит
    t = js(page, "(() => { " + DUMMY + " applyElem(d, 'fire', 100, 'fire'); return d.st.fire.t; })()")
    assert abs(t - 3) < 0.05


def test_poison_rune_antiheal(page):
    run(page, BASE)
    assert js(page, "(() => { const d = G.dummy; d.st = {rcd:{}, poison:{n:5, t:4, dps:1, tick:0.5}}; return elemHealMul(d); })()") == 0.5
    run(page, f"S.runes.w[1] = {R % ('poison', 5)}; refreshStats();")
    assert abs(js(page, "ST.elV.poison") - 0.24) < 1e-9
    assert abs(js(page, "(() => { const d = G.dummy; d.st = {rcd:{}, poison:{n:5, t:4, dps:1, tick:0.5}}; return elemHealMul(d); })()") - 0.25) < 1e-9
    assert js(page, "(() => { const d = G.dummy; d.st = {rcd:{}, poison:{n:1, t:4, dps:1, tick:0.5}}; return elemHealMul(d); })()") < 0.5


def test_poison_armor(page):
    run(page, BASE)
    c0, p0 = js(page, "ST.curseRes"), js(page, "ST.res.poison")
    assert js(page, f"(() => {{ S.runes.a[1] = {R % ('poison', 5)}; refreshStats(); hero.hpoison = null; applyElemEffect('poison', 100); return hero.hpoison; }})()") is None
    assert abs(js(page, "ST.curseRes") - (c0 + 0.2)) < 1e-9 and abs(js(page, "ST.res.poison") - (p0 + 0.2)) < 1e-9


def test_poisoned_hit_weaker(page):
    run(page, BASE + "Math.random = () => 0.99;")
    hit = "(() => { const e = {x: hero.x + 30, y: hero.y, st: {rcd:{}, poison:{n:1, t:3, dps:0, tick:0.5}}}; hero.dead = false; hero.hp = 1e9; hero.shield = 0; hero.iframe = 0; hero.dashT = 0; const h0 = hero.hp; damageHero(1000, e); return h0 - hero.hp; })()"
    a = js(page, hit)
    run(page, f"S.brace.lvl = 1; S.runes.j[1] = {R % ('poison', 5)}; refreshStats();")
    b = js(page, hit)
    assert abs(b / a - 0.85) < 1e-6


def test_runes_off_in_tower_entry(page):
    run(page, BASE + f"S.tower.charges = 2; S.runes.a[0] = {R % ('elem', 5)}; S.runes.w[1] = {R % ('elem', 5)}; refreshStats();")
    out = js(page, "ST.res.fire")
    assert out >= 0.16
    run(page, "towerEnter(1, 1);")
    assert js(page, "S.loc") == 4
    assert js(page, "ST.res.fire") == 0 and js(page, "ST.ru.zapChance || 0") == 0
    run(page, "towerExit(false);")
    assert abs(js(page, "ST.res.fire") - out) < 1e-9

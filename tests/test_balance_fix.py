"""Этап 1.1: стак горит силой своего удара, молния/танец по одинокой цели, «Острота», 4-й слот бижутерии и Печать Четырёх Ветров, строка стихий у чучела."""
import pytest
from conftest import js, run

BASE = "runCmd('unlock3'); travelTo(3); fixSlots(); refreshStats(); G.speed = 0.0001;"


def test_burn_stack_uses_own_hit(page):
    run(page, BASE + "S.w.ench = [{id:'burn',t:5,v:36},{id:'poison',t:5,v:32},null,null]; refreshStats();")
    r = js(page, """(() => { const d = G.dummy; d.st = null; for (let i = 0; i < 4; i++) { applyElem(d, 'fire', 100, 'fire'); applyElem(d, 'poison', 100, 'poison'); }
      applyElem(d, 'fire', 1000, 'fire'); applyElem(d, 'poison', 1000, 'poison'); return [d.st.fire.dps / ST.elV.fire, d.st.poison.dps / ST.elV.poison, d.st.fire.n]; })()""")
    assert r[2] == 5
    assert abs(r[0] - 280) < 1e-6      # 100 → 1000 одним стаком из пяти: сдвиг на 1/5, а не максимум (1000)
    assert abs(r[1] - 280) < 1e-6


def test_multi_stack_weight(page):
    run(page, BASE + "S.w.ench = [{id:'burn',t:5,v:36},null,null,null]; refreshStats();")
    r = js(page, "(() => { const d = G.dummy; d.st = null; applyElem(d, 'fire', 0, 'fire', {dps: 10}); applyElem(d, 'fire', 0, 'fire', {dps: 50, n: 3}); return [d.st.fire.n, d.st.fire.dps]; })()")
    assert r[0] == 4 and abs(r[1] - 40) < 1e-9     # 1 стак по 10 + 3 стака по 50 → средняя 40


def test_chain_hits_lone_target(page):
    run(page, BASE + "S.w.ench = [{id:'chain',t:5,v:30},null,null,null]; refreshStats();")
    r = js(page, "(() => { const d = G.dummy; G.enemies = [d]; d.hp = d.maxHp = 1e15; G.dsess = null; chainLightning(d, 3, 1000); return [G.dsess && G.dsess.tot.chain > 0, !!(d.st && d.st.zap && d.st.zap.t > 0)]; })()")
    assert r == [True, True]


def test_chain_prefers_neighbours(page):
    run(page, BASE)
    r = js(page, "(() => { const d = G.dummy; d.hp = d.maxHp = 1e15; const n = Object.assign({}, d, { dummy: false, x: d.x + 100, hp: 1e15, maxHp: 1e15, st: null }); G.enemies = [d, n]; G.dsess = null; chainLightning(d, 1, 1000); return [!!(G.dsess && G.dsess.tot.chain), n.hp < 1e15]; })()")
    assert r == [False, True]          # сосед есть — цель сама молнией не бьётся


def test_shadow_hits_lone_target(page):
    run(page, BASE)
    r = js(page, "(() => { const d = G.dummy; G.enemies = [d]; d.hp = d.maxHp = 1e15; G.dsess = null; hero.x = d.x - 60; hero.y = d.y; hero.shadowCd = 0; shadowDance(d); return !!(G.dsess && G.dsess.tot.shadow > 0); })()")
    assert r is True


def test_sharp_enchant(page):
    run(page, BASE + "S.ring.lvl = 15; fixSlots(); S.ring.ench[0] = {id:'sharp',t:5,v:22,v2:50}; refreshStats();")
    assert js(page, "ENCH.sharp.slot") == 'j'
    assert abs(js(page, "ST.sharp") - 0.22) < 1e-9
    c0 = js(page, "(() => { S.ring.ench[0] = null; refreshStats(); return ST.critDmg; })()")
    c1 = js(page, "(() => { S.ring.ench[0] = {id:'sharp',t:5,v:22,v2:50}; refreshStats(); return ST.critDmg; })()")
    assert abs(c1 - c0 - 0.5) < 1e-9
    assert js(page, "[physMul({}), physMul({src:'whirl'}), physMul({src:'wave'}), physMul({src:'shadow'}), physMul({src:'aura'})]") == [1.22] * 5
    assert js(page, "[physMul({src:'chain', el:'thunder'}), physMul({src:'oni', el:'dark'}), physMul({src:'react'}), physMul({src:'pet'})]") == [1, 1, 1, 1]


def test_sharp_rolls_from_forge(page):
    run(page, BASE)
    e = js(page, "rollEnch('sharp')")
    assert e['id'] == 'sharp' and e['v'] > 0 and e['v2'] > 0


def test_jewel_slot4_needs_seal_and_price(page):
    run(page, BASE + "G.speed = 1; S.ring.lvl = 15; S.ring.slot4 = false; fixSlots(); S.gold = 3e8; S.jade = 300; S.jSeal = 0; refreshStats();")
    assert js(page, "S.ring.ench.length") == 3
    run(page, "forgeAction('jslot4', 'ring', null, null);")
    assert js(page, "[S.ring.slot4, S.gold, S.jade]") == [False, 3e8, 300]
    run(page, "S.jSeal = 1; forgeAction('jslot4', 'ring', null, null);")
    assert js(page, "[S.ring.slot4, S.ring.ench.length, S.jSeal, S.gold, S.jade]") == [True, 4, 0, 5e7, 50]
    run(page, "save();"); page.reload(); page.wait_for_function("typeof S==='object' && S.ring", polling=100)
    assert js(page, "[S.ring.slot4, S.ring.ench.length]") == [True, 4]


def test_jewel_slot4_only_at_15(page):
    run(page, BASE + "S.brace.lvl = 14; S.brace.slot4 = false; fixSlots(); S.gold = 3e8; S.jade = 300; S.jSeal = 2;")
    run(page, "forgeAction('jslot4', 'brace', null, null);")
    assert js(page, "[S.brace.slot4, S.brace.ench.length, S.jSeal]") == [False, 3, 2]


def test_jewel_tab_shows_slot4(page):
    run(page, BASE + "G.speed = 1; S.ring.lvl = 15; S.ring.slot4 = false; fixSlots(); S.jSeal = 1; S.gold = 3e8; S.jade = 300; openForge(); G.forgeTab = 'j'; G.jewelSel = 'ring'; renderForge();")
    assert page.locator('#forge [data-act="jslot4"]').count() == 1
    assert 'Печать Четырёх Ветров' in page.inner_text('#forge')


def test_seal_from_trials(page):
    run(page, BASE + "G.speed = 1; S.sealN = 24; S.jSeal = 0; S.daily = null; const q = genTrial(); q.done = true; S.quests.active = [q]; openBoard(); renderBoard();")
    page.click('#board [data-act="claim"]')
    assert js(page, "[S.jSeal, S.sealN]") == [1, 0]


def test_seal_counter_skips_over_limit_trials(page):
    run(page, BASE + "G.speed = 1; S.sealN = 24; S.jSeal = 0; daily().trials = DAILY.trials; const q = genTrial(); q.done = true; S.quests.active = [q]; openBoard(); renderBoard();")
    page.click('#board [data-act="claim"]')
    assert js(page, "[S.jSeal, S.sealN]") == [0, 24]


def test_seal_counter_on_board(page):
    run(page, BASE + "G.speed = 1; S.sealN = 7; openBoard(); G.boardTab = 'trials'; renderBoard();")
    assert 'до Печати Четырёх Ветров: 18' in page.inner_text('#board')


def test_old_save_defaults(page):
    run(page, "delete S.jSeal; delete S.sealN; delete S.ring.slot4; fixSlots();")
    assert js(page, "[S.jSeal, S.sealN, S.ring.slot4]") == [0, 0, False]


def test_dummy_panel_element_share(page):
    assert js(page, "dummyElemShare({ tot: { katana: 600, fire: 300, chain: 100, whirl: 0 }, sum: 1000 })") == pytest.approx(0.4)
    assert js(page, "dummyElemShare(null)") == 0

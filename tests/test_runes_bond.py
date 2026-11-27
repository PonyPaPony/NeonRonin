"""Руны 2а, задача 6: «Узы» — второй навык питомца на уровнях ветки, место руны решает какие, ранг — силу."""
from conftest import js, run

BASE = ("runCmd('unlock3'); S.tower.unlocked = true; travelTo(3); fixSlots(); refreshStats(); G.speed = 0.0001;"
        "S.pets.owned.cat = {lvl: 43, xp: 0, picks: [0, 0, null, null, null, null]}; S.pets.active = 'cat'; fixPets(); refreshPetFx(); refreshStats();")
R = "{id:'%s', r:%d, f:[0,0,0,0,0,0]}"


def test_bond_unlocks_second_pick(page):
    run(page, BASE + "S.pets.owned.cat.x2 = [null, 1];")
    assert js(page, "PFX.atkDmg || 0") == 0                          # без руны второй выбор хранится, но не действует
    run(page, f"S.runes.w[0] = {R % ('bond', 0)}; refreshPetFx(); refreshStats();")
    assert abs(js(page, "PFX.atkDmg") - 0.6 * 0.4) < 1e-9 and js(page, "PFX.atkN") == 1
    assert abs(js(page, "PFX.gold") - 0.06) < 1e-9                    # основной выбор — в полную силу
    run(page, "S.runes.w[0].r = 5; refreshPetFx();")
    assert abs(js(page, "PFX.atkDmg") - 0.6) < 1e-9


def test_bond_place_tiers(page):
    run(page, BASE)
    run(page, f"S.runes.a[0] = {R % ('bond', 5)}; refreshPetFx();")
    assert js(page, "Object.keys(bondTiers()).map(Number)") == [2, 3]
    run(page, f"S.runes.a[0] = null; S.ring.lvl = 1; S.runes.j[0] = {R % ('bond', 5)}; refreshPetFx();")
    assert js(page, "Object.keys(bondTiers()).map(Number)") == [4]
    run(page, f"S.runes.w[0] = {R % ('bond', 2)}; refreshPetFx();")
    assert js(page, "bondTiers()") == {'0': 2, '1': 2, '4': 5}         # ульта (индекс 5) — никогда


def test_bond_int_round(page):
    run(page, BASE + "S.pets.owned.cat.picks = [0, 1, 0, null, null, null]; S.pets.owned.cat.x2 = [null, null, 1];" + f"S.runes.a[0] = {R % ('bond', 0)}; refreshPetFx();")
    assert js(page, "PFX.atkN") == 1 + 1                               # «Царапки» +2 цели × 0,4 → не меньше 1


def test_bond_pick_and_respec_ui(page):
    run(page, BASE + f"S.runes.w[0] = {R % ('bond', 3)}; S.jade = 1e6; refreshPetFx(); openPets(); G.petSel = 'cat'; renderPets();")
    btn = page.locator("#pt-right [data-act='pick2'][data-i='1'][data-k='1']")
    assert btn.count() == 1 and btn.is_enabled()
    assert '絆' in btn.inner_text()
    btn.click()
    assert js(page, "S.pets.owned.cat.x2[1]") == 1 and js(page, "PFX.atkDmg > 0") is True
    page.locator("#pt-right [data-act='presp']").click()
    assert js(page, "S.pets.owned.cat.x2") == [] and js(page, "S.pets.owned.cat.picks") == []


def test_bond_off_in_tower(page):
    run(page, BASE + f"S.pets.owned.pony = {{lvl: 20, xp: 0, picks: [0, 0, null, null, null, null], x2: [1, 1]}}; S.pets.active = 'pony'; S.runes.w[0] = {R % ('bond', 5)}; S.tower.charges = 2; refreshPetFx();")
    assert js(page, "Object.keys(bondTiers()).length") == 2
    run(page, "towerEnter(1, 1);")
    assert js(page, "Object.keys(bondTiers()).length") == 0 and js(page, "Object.keys(PFX).filter(k => k !== 'ult').length") == 0

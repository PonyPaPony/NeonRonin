"""Руны 2а, задача 1: данные, сейв, ковка/вставка/переброс/огранка/извлечение/разбор, правила слотов."""
from conftest import js, run, load_save

BASE = "runCmd('unlock3'); S.tower.unlocked = true; travelTo(3); fixSlots(); refreshStats(); G.speed = 0.0001; S.village.peakGM = 1000; S.gold = 1e15;"
GIVE = "S.runes.bag.push({id:%r, r:%d, f:[0,0,0,0,0,0]});"


def test_rv_formula(page):
    assert js(page, "rv(4, 16, 0)") == 4
    assert js(page, "rv(4, 16, 5)") == 16
    assert abs(js(page, "rv(4, 16, 2)") - (4 + 12 * 0.9 / 3)) < 1e-9
    assert abs(js(page, "rv(8, 3, 5)") - 3) < 1e-9


def test_default_and_old_saves(page, V6):
    load_save(page, V6)
    r = js(page, "S.runes")
    assert r['frag'] == [0] * 6 and r['bag'] == [] and r['w'] == [None] * 3 and r['a'] == [None] * 3 and r['j'] == [None] * 3
    d = dict(V6)
    d['runes'] = {'frag': [-3, 'x', 2.7, 5, None, 1], 'bag': [{'id': 'zzz', 'r': 1}, {'id': 'spirit', 'r': 9}, {'id': 'heart', 'r': 2}],
                  'w': [{'id': 'spirit', 'r': 1}, {'id': 'spirit', 'r': 2}, None], 'a': 'bad', 'j': [None]}
    load_save(page, d)
    r = js(page, "S.runes")
    assert r['frag'] == [0, 0, 2, 5, 0, 1]
    assert [b['id'] for b in r['bag']] == ['heart', 'spirit']     # мусор удалён, дубликат вида из катаны — в сумку
    assert r['w'][0]['id'] == 'spirit' and r['w'][1] is None
    assert r['a'] == [None] * 3 and r['j'] == [None] * 3


def test_forge_rune(page):
    run(page, BASE + "S.runes.frag[2] = 10;")
    assert js(page, "runeForge(2)") is True
    r = js(page, "S.runes")
    assert r['frag'][2] == 0 and len(r['bag']) == 1 and r['bag'][0]['r'] == 2 and r['bag'][0]['f'][2] == 10
    assert r['bag'][0]['id'] in js(page, "Object.keys(RUNES)")
    run(page, "S.runes.frag[2] = 9;")
    assert js(page, "runeForge(2)") is False


def test_insert_rules(page):
    run(page, BASE + GIVE % ('spirit', 0) + GIVE % ('spirit', 0))
    assert js(page, "runeInsert(0, 'w', 0)") is True
    assert js(page, "runeInsert(0, 'w', 1)") is False                # вторая руна того же вида в предмете
    run(page, "S.runes.bag = [];" + GIVE % ('elem', 0) * 3)
    assert js(page, "runeInsert(0, 'a', 0) && runeInsert(0, 'a', 1) && runeInsert(0, 'a', 2)") is True   # Стихия — во все три слота
    run(page, "S.ring.lvl = 1; S.brace.lvl = 1; S.runes.bag = [];" + GIVE % ('poison', 0) * 2)
    assert js(page, "runeInsert(0, 'j', 0)") is True
    assert js(page, "runeInsert(0, 'j', 1)") is False                # бижутерия — один набор


def test_insert_cost(page):
    run(page, BASE)
    assert js(page, "villageGM()") == 1000
    assert js(page, "runeInsertCost('w', 0, 0)") == 400 * 1000
    run(page, "S.runes.w = [{id:'spirit',r:0,f:[0,0,0,0,0,0]}, {id:'heart',r:0,f:[0,0,0,0,0,0]}, null];")
    assert js(page, "runeInsertCost('w', 2, 3)") == 400 * 1000 * 8 * 4
    g0 = js(page, "S.gold")
    run(page, GIVE % ('pierce', 3) + "runeInsert(0, 'w', 2);")
    assert g0 - js(page, "S.gold") == 400 * 1000 * 8 * 4


def test_extract_free_and_reroll(page):
    run(page, BASE + GIVE % ('spirit', 1) + "runeInsert(0, 'w', 0);")
    g0 = js(page, "S.gold")
    assert js(page, "runeExtract('w', 0)") is True
    assert js(page, "S.gold") == g0 and js(page, "S.runes.bag.length") == 1 and js(page, "S.runes.w[0]") is None
    run(page, "runeInsert(0, 'w', 0); S.runes.frag[1] = 100;")
    c = js(page, "runeInsertCost('w', 0, 1)")
    g0 = js(page, "S.gold")
    assert js(page, "runeReroll('w', 0)") is True
    w = js(page, "S.runes.w[0]")
    assert w['id'] != 'spirit' and w['r'] == 1
    assert js(page, "S.runes.frag[1]") == 97 and abs((g0 - js(page, "S.gold")) - c * 0.25) <= 1
    g0 = js(page, "S.gold")
    to = 'time' if w['id'] != 'time' else 'shade'
    assert js(page, f"runeReroll('w', 0, '{to}')") is True
    assert js(page, "S.runes.w[0].id") == to and js(page, "S.runes.frag[1]") == 82 and abs((g0 - js(page, "S.gold")) - c * 1.25) <= 1


def test_upgrade(page):
    run(page, BASE + GIVE % ('spirit', 1) + "runeInsert(0, 'w', 0); S.runes.frag[2] = 25;")
    c = js(page, "runeInsertCost('w', 0, 2)")
    g0 = js(page, "S.gold")
    assert js(page, "runeUpgrade('w', 0)") is True
    w = js(page, "S.runes.w[0]")
    assert w['r'] == 2 and w['id'] == 'spirit' and w['f'][2] == 20 and js(page, "S.runes.frag[2]") == 5
    assert g0 - js(page, "S.gold") == c
    run(page, "S.runes.w[0].r = 5; S.runes.frag = [99,99,99,99,99,99];")
    assert js(page, "runeUpgrade('w', 0)") is False


def test_scrap_30(page):
    run(page, BASE + "S.runes.bag.push({id:'spirit', r:2, f:[10,0,20,0,0,0]});")
    assert js(page, "runeScrap(0)") is True
    assert js(page, "S.runes.frag") == [3, 0, 6, 0, 0, 0] and js(page, "S.runes.bag.length") == 0


def test_bag_full_blocks(page):
    run(page, BASE + "for (let i = 0; i < 40; i++) S.runes.bag.push({id:'time', r:0, f:[10,0,0,0,0,0]}); S.runes.w[0] = {id:'spirit', r:0, f:[10,0,0,0,0,0]}; S.runes.frag[0] = 10;")
    assert js(page, "runeExtract('w', 0)") is False
    assert js(page, "S.runes.w[0].id") == 'spirit'
    assert js(page, "runeForge(0)") is False
    assert js(page, "S.runes.frag[0]") == 10 and js(page, "S.runes.bag.length") == 40


def test_runes_survive_tower_reload(page):
    run(page, BASE + "S.tower.charges = 2; S.runes.w[0] = {id:'spirit', r:3, f:[0,0,0,0,0,0]}; S.runes.frag[4] = 7; save(); towerEnter(1, 1);")
    assert js(page, "S.loc") == 4
    run(page, "save(); G.noSaveOnUnload = true;")
    page.reload()
    page.wait_for_function("typeof S==='object' && typeof hero==='object'", polling=100, timeout=15000)
    assert js(page, "!S.mainStash && S.loc !== 4") is True
    assert js(page, "S.runes.w[0].id") == 'spirit' and js(page, "S.runes.frag[4]") == 7
    assert js(page, "S.runes.bag.length") == 0 and js(page, "runesOn()") is True


def test_oni_awaken_keeps_runes(page):
    run(page, BASE + "S.ring.lvl = 3; S.runes.j[0] = {id:'time', r:2, f:[0,0,0,0,0,0]}; S.runes.w[1] = {id:'heart', r:1, f:[0,0,0,0,0,0]}; oniAwaken();")
    assert js(page, "S.runes.j[0].id") == 'time' and js(page, "S.runes.w[1].id") == 'heart'
    assert js(page, "runeAt('j', 0)") is None
    run(page, "S.ring.lvl = 1;")
    assert js(page, "runeAt('j', 0).id") == 'time'


def test_runes_on_flags(page):
    run(page, "runCmd('unlock3'); travelTo(3); S.tower.unlocked = false;")
    assert js(page, "runesOn()") is False
    run(page, "S.tower.unlocked = true;")
    assert js(page, "runesOn()") is True
    run(page, "S.mainStash = {};")
    assert js(page, "runesOn()") is False
    run(page, "delete S.mainStash; S.loc = 4;")
    assert js(page, "runesOn()") is False

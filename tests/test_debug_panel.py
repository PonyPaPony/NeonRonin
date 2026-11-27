"""Панель отладки (консоль 2.0): «божественные» команды, Мидас, руны, панель кнопок."""
from conftest import js, run, frames

UNL = "runCmd('unlock3'); runCmd('tower'); travelTo(3); fixSlots(); refreshStats();"


def test_god_weapon_and_armor(page):
    run(page, UNL + "S.w.ench = [{id:'crit', t:1, v:5}, null, null, null]; S.a.ench = [{id:'vigor', t:2, v:5}, null, null, null];")
    run(page, "runCmd('клинок бога'); runCmd('доспех бога');")
    w = js(page, "S.w"); a = js(page, "S.a")
    assert w['rank'] == 12 and w['lvl'] == 8 and a['rank'] == 12 and a['lvl'] == 8
    assert len(w['ench']) == 4 and w['ench'][1] is None
    assert w['ench'][0]['t'] == 5 and abs(w['ench'][0]['v'] - js(page, "round1(ENCH.crit.vals[4] * 1.15 * 1.27)")) < 1e-9
    assert a['ench'][0]['t'] == 5


def test_god_jewel(page):
    run(page, UNL + "runCmd('бижутерия бога');")
    r = js(page, "JKEYS.map(k => [S[k].lvl, S[k].slot4, S[k].ench.length])")
    assert r == [[15, True, 4]] * 3


def test_god_soul_stars_tree(page):
    run(page, UNL + "runCmd('душа бога');")
    assert js(page, "soulTotal() === SOUL_TOTAL") is True
    s0 = js(page, "starsTotal()")
    run(page, "runCmd('звёзды 10');")
    assert js(page, "starsTotal()") == s0 + 10
    run(page, "runCmd('древо бога');")
    assert js(page, "TREE.every(n => S.tree[n.id] === n.max)") is True


def test_prosperity(page):
    run(page, UNL + "runCmd('процветание');")
    assert js(page, "VILLAGE.every(b => S.village.steps[b.id] === V_MAX) && S.village.crystal && S.village.queue.length === 0") is True


def test_midas_keeps_resources(page):
    run(page, UNL + "S.gold = 5; S.souls = 0; S.jade = 0; S.runes.frag = [0,0,0,0,0,0]; runCmd('мидас');")
    assert js(page, "SET.midas") is True
    page.wait_for_timeout(350)
    assert js(page, "S.gold >= 1e15 && S.souls >= 1e15 && S.jade >= 1e15 && S.dew >= 1e6 && S.xp >= 1e15 && S.runes.frag.every(f => f >= 999)") is True
    assert js(page, "!document.querySelector('#midas-tag').classList.contains('hidden')") is True
    run(page, "runeForge(5);")
    page.wait_for_timeout(350)
    assert js(page, "S.runes.frag[5] >= 999") is True
    run(page, "runCmd('мидас');")
    assert js(page, "SET.midas") is False and js(page, "document.querySelector('#midas-tag').classList.contains('hidden')") is True
    assert js(page, "'midas' in JSON.parse(localStorage.getItem(CFG.SAVE_KEY))") is False


def test_tower_level_and_open_all(page):
    run(page, "runCmd('открыть всё');")
    assert js(page, "S.unlock2 && S.unlock3 && S.tower.unlocked") is True
    run(page, "runCmd('twlvl 15');")
    assert js(page, "towerMaxLvl() >= 15 && S.tower.lvlSel === 15") is True


def test_panel_buttons(page):
    run(page, "SET.console = true; toggleConsole(true);")
    txt = page.inner_text('#console')
    for w in ['ГЕРОИНЯ', 'ОНИ', 'МИР', 'БАШНЯ', 'ЭКОНОМИКА', 'РУНЫ', 'Клинок Бога', 'Мидас', 'Процветание']:
        assert w in txt
    run(page, "runCmd('открыть всё');")
    page.click("#console [data-cmd='rune spirit 5']")
    assert js(page, "S.runes.bag.some(x => x.id === 'spirit' && x.r === 5)") is True
    page.click("#console [data-cmd='rfrag all 100']")
    assert js(page, "S.runes.frag.every(f => f >= 100)") is True
    page.click("#console [data-cmd='клинок бога']")
    assert js(page, "S.w.rank") == 12
    run(page, "runCmd('rank_weapon 3');")                          # старые команды живы
    assert js(page, "S.w.rank") == 3

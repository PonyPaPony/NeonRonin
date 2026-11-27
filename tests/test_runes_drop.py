"""Руны 2а, задача 2: фрагменты рун падают в Башне, ранг по этажу и уровню, подбор в основной сейв."""
from conftest import js, run, frames

UNL = "runCmd('unlock3'); S.tower.unlocked = true; travelTo(3); fixSlots(); refreshStats();"


def test_frag_rank_by_floor(page):
    run(page, UNL + "window.__r = 0.99; Math.random = () => window.__r;")
    got = js(page, "[10, 11, 25, 26, 40, 41, 60, 61, 80, 81, 100].map(f => runeFragRank(f, 99))")
    assert got == [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    run(page, "window.__r = 0;")
    assert js(page, "[1, 41, 100].map(f => runeFragRank(f, 99))") == [1, 4, 5]
    run(page, "window.__r = 0.39;")
    assert js(page, "runeFragRank(1, 99)") == 1                     # шанс +1 ранга ограничен 40%
    run(page, "window.__r = 0.41;")
    assert js(page, "runeFragRank(1, 99)") == 0


def test_frag_rank_capped_by_tower_level(page):
    run(page, UNL + "window.__r = 0.99; Math.random = () => window.__r;")
    assert js(page, "[1, 2, 3, 7, 8, 14, 15, 24, 25].map(l => runeFragRank(100, l))") == [1, 1, 2, 2, 3, 3, 4, 4, 5]
    assert js(page, "[1, 3, 8, 15, 25].map(runeFragCap)") == [1, 2, 3, 4, 5]
    run(page, "window.__r = 0;")
    assert js(page, "runeFragRank(51, 8)") == 3                     # шанс ранга выше не пробивает потолок
    assert js(page, "runeFragRank(1, 8)") == 1


def test_tower_tab_shows_frag_cap(page):
    run(page, UNL + "S.tower.charges = 2; S.tower.kills = 80000; G.twLvl = 8; openTravel(); G.travelTab = 'tower'; renderTravel();")
    txt = page.inner_text('#travel')
    assert 'Эпический' in txt and 'фрагменты рун' in txt.lower()


def test_frag_drop_rates(page):
    run(page, UNL + "S.tower.charges = 2; towerEnter(1, 1); window.__r = 0.01; Math.random = () => window.__r;")
    cnt = "(e => { G.loot.length = 0; runeFragDrop(e); return G.loot.filter(l => l.type === 'rfrag').length; })"
    assert js(page, cnt + "({x: 2000, y: 1700})") == 1
    run(page, "window.__r = 0.02;")
    assert js(page, cnt + "({x: 2000, y: 1700})") == 0
    run(page, "window.__r = 0.09;")
    assert js(page, cnt + "({x: 2000, y: 1700, elite: true})") == 1
    run(page, "window.__r = 0.99;")
    assert js(page, cnt + "({x: 2000, y: 1700, mini: true})") == 2
    assert js(page, cnt + "({x: 2000, y: 1700, boss: true})") == 5


def test_frag_drop_from_tower_kill(page):
    run(page, UNL + "S.tower.charges = 2; towerEnter(1, 1); Math.random = () => 0.001;")
    r = js(page, "(() => { G.loot.length = 0; const e = makeTowerMob('bruiser', hero.x + 50, hero.y, false); G.enemies.push(e); killEnemy(e); return G.loot.filter(l => l.type === 'rfrag').length; })()")
    assert r == 1


def test_frag_pickup_goes_to_main(page):
    run(page, UNL + "S.tower.charges = 2; towerEnter(1, 1); G.enemies.length = 0; G.loot.length = 0; dropLoot('rfrag', hero.x, hero.y, 3); G.loot[0].t = 1; G.loot[0].z = 0; G.loot[0].vz = 0;")
    frames(page, 20)
    assert js(page, "S.runes.frag[3]") == 1
    assert js(page, "TOWER_KEYS.includes('runes') || 'runes' in (S.mainStash || {})") is False
    run(page, "towerExit(false);")
    assert js(page, "S.runes.frag[3]") == 1


def test_frag_draw_no_white(page):
    run(page, UNL)
    seen = js(page, """(() => { const c = document.createElement('canvas').getContext('2d'), seen = [], d = Object.getOwnPropertyDescriptor(CanvasRenderingContext2D.prototype, 'fillStyle');
      Object.defineProperty(c, 'fillStyle', { set(v) { seen.push(String(v)); d.set.call(c, v); }, get() { return d.get.call(c); } });
      G.loot.length = 0; for (let i = 0; i < 20; i++) G.loot.push({ type: 'rfrag', x: hero.x + i * 5, y: hero.y, z: 0, val: i % 6, t: 1, spin: i });
      G.view = { x0: hero.x - 500, x1: hero.x + 500, y0: hero.y - 500, y1: hero.y + 500 }; drawLoot(c, 1.3); return seen; })()""")
    assert any('#ff6a3c' in x or '255,106,60' in x.replace(' ', '') for x in seen), 'кристаллы цвета ранга не нарисованы'
    bad = [s for s in seen if s.lower() in ('#fff', '#ffffff', 'white') or s.replace(' ', '').startswith('rgba(255,255,255')]
    assert bad == []

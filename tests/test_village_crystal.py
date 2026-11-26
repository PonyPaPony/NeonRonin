from conftest import js, run, load_save, frames

KILL_BOSS = """(z => { const b = makeBoss(z); G.enemies.push(b); killEnemy(b); return G.loot.filter(l => l.type === 'vshard').length; })"""
PICK = "() => { for (const l of G.loot) { l.x = hero.x; l.y = hero.y; l.t = 1; l.z = 0; } }"
SPY = """() => { window.__txt = []; const f = CanvasRenderingContext2D.prototype.fillText;
  if (!window.__spy) { window.__spy = true; CanvasRenderingContext2D.prototype.fillText = function (t, ...a) { if (window.__txt) window.__txt.push(String(t)); return f.call(this, t, ...a); }; } }"""


def test_tokyo_boss_drops_shard_once(page):
    run(page, "G.loot.length = 0;")
    assert page.evaluate(KILL_BOSS, 2) == 1
    page.evaluate(PICK); frames(page, 6)
    assert js(page, "S.village.shards") == [False, True, False, False]
    run(page, "G.loot.length = 0;")
    assert page.evaluate(KILL_BOSS, 2) == 0


def test_shard_never_expires_and_flies(page):
    run(page, "G.loot.length = 0;")
    page.evaluate(KILL_BOSS, 1)
    assert js(page, "G.loot.find(l => l.type === 'vshard').attract") is True


def test_no_shard_outside_tokyo(page):
    run(page, "runCmd('unlock'); travelTo(2); G.loot.length = 0;")
    assert page.evaluate(KILL_BOSS, 1) == 0


def test_four_shards_light_crystal(page):
    run(page, "for (const z of [1,2,3,4]) vOnShard(z);")
    assert js(page, "S.village.crystal") is True
    assert "Барьер древних богов" in js(page, "G.banner.text")


def test_shard_toast_counts(page):
    run(page, "vOnShard(3);")
    assert "Осколок кристалла 1/4" in page.inner_text('#toasts')


def test_intro_once_for_old_save(page, V6):
    load_save(page, V6)
    page.wait_for_selector('#vl-say:not(.hidden)', timeout=4000)
    assert "осколк" in page.inner_text('#vl-say').lower()
    page.click('#vl-say [data-act="ok"]')
    run(page, "save(); G.noSaveOnUnload = true;")
    page.reload(); page.wait_for_function("typeof S==='object' && S.village", polling=100, timeout=15000)
    page.wait_for_timeout(2500)
    assert js(page, "document.querySelector('#vl-say').classList.contains('hidden')") is True


def test_no_intro_for_new_player(page):
    page.wait_for_timeout(2500)
    assert js(page, "document.querySelector('#vl-say').classList.contains('hidden')") is True


def test_crystal_scene_no_white_flash(page):
    run(page, "window.__fl = 0; setInterval(() => { if (G.flash > 0.15) window.__fl++; for (const e of G.enemies) if (e.boss && e.flash > 0) window.__fl++; }, 16); for (const z of [1,2,3,4]) vOnShard(z);")
    page.wait_for_timeout(3000)
    assert js(page, "window.__fl") == 0


def test_tracker_shows_shards(page):
    run(page, "vOnShard(1);")
    page.evaluate(SPY); frames(page, 4)
    assert any("Собери осколки кристалла у 4 стражей Токио (1/4)" in t for t in js(page, "window.__txt"))
    run(page, "for (const z of [2,3,4]) vOnShard(z);")
    page.evaluate(SPY); frames(page, 4)
    assert not any("Собери осколки" in t for t in js(page, "window.__txt"))


def test_boss_shows_crystal_until_taken(page):
    assert js(page, "vBossHasShard({ boss: true, loc: 1, z: 2 })") is True
    run(page, "vOnShard(2);")
    assert js(page, "vBossHasShard({ boss: true, loc: 1, z: 2 })") is False
    assert js(page, "vBossHasShard({ boss: true, loc: 2, z: 1 })") is False

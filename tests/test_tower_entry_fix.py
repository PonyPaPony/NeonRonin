from conftest import js, run, frames, load_save


def _entry(page, setup):
    run(page, "for (const s of SOUL) S.soul[s.id] = SOUL_MAX; " + setup + " refreshStats(); save();")
    run(page, "towerEnter(1, 1);"); frames(page, 10)   # без ручного refreshStats
    return js(page, "[ST.dmg, ST.maxHp, hero.hp]")


def test_tower_entry_ignores_stars(page, V6):
    load_save(page, V6)
    clean = _entry(page, "S.stars.b.pow = 0; S.stars.b.vit = 0; S.stars.peak = 0;")
    run(page, "towerExit();"); frames(page, 5)
    withs = _entry(page, "S.stars.b.pow = 30; S.stars.b.vit = 30; S.stars.peak = 50;")
    assert abs(withs[0] - clean[0]) < 1e-9 and abs(withs[1] - clean[1]) < 1e-9 and withs[2] <= clean[1] + 1e-9


def test_tower_entry_ignores_village(page, V6):
    load_save(page, V6)
    clean = _entry(page, "")
    run(page, "towerExit();"); frames(page, 5)
    withv = _entry(page, "S.village.crystal = true; S.village.steps.tower1 = 3; S.village.steps.tower2 = 3;")
    assert abs(withv[1] - clean[1]) < 1e-9

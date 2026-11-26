from conftest import js, run, load_save

FULL = "for (const s of SOUL) S.soul[s.id] = SOUL_MAX;"


def test_v6_has_no_stars(page, V6):
    load_save(page, V6)
    assert js(page, "S.stars.b.pow") == 0 and js(page, "S.stars.peak") == 0 and js(page, "S.stars.spent") == 0


def test_star_cost_curve(page):
    assert js(page, "starCost(0)") == 1200000
    assert js(page, "starCost(9)") == round(1200000 * 1.025 ** 9)


def test_stars_open_only_full(page):
    run(page, "for (const s of SOUL) S.soul[s.id] = SOUL_MAX; S.soul.pow = 19;")
    assert js(page, "starsOpen()") is False
    run(page, FULL)
    assert js(page, "starsOpen()") is True


def test_star_bonuses(page):
    run(page, FULL + " refreshStats();")
    d0, h0, c0 = js(page, "[ST.dmg, ST.maxHp, ST.critChance]")
    run(page, "S.stars.b.pow = 3; S.stars.b.vit = 2; S.stars.b.acc = 4; refreshStats();")
    d1, h1, c1 = js(page, "[ST.dmg, ST.maxHp, ST.critChance]")
    assert abs(d1 / d0 - (1 + 21 * 0.06) / (1 + 20 * 0.06)) < 1e-9
    assert abs(h1 / h0 - (1 + (20 + 2 / 3) * 0.075) / (1 + 20 * 0.075)) < 1e-9
    assert abs(c1 - c0 - 0.01) < 1e-9


def test_constellation_bonus(page):
    run(page, FULL + " refreshStats();")
    d0, h0 = js(page, "[ST.dmg, ST.maxHp]")
    run(page, "S.stars.peak = 25; refreshStats();")
    assert js(page, "constN()") == 2
    d1, h1 = js(page, "[ST.dmg, ST.maxHp]")
    assert abs(d1 / d0 - 1.02) < 1e-9 and abs(h1 / h0 - 1.02) < 1e-9


def test_caps_respected(page):
    run(page, FULL + " S.stars.b.def = 9999; S.stars.b.acc = 99999; refreshStats();")
    assert js(page, "ST.reduce") <= 0.75 and js(page, "ST.critChance") <= 1


def test_tower_ignores_stars(page, V6):
    load_save(page, V6)
    run(page, FULL + " S.stars.b.pow = 30; S.stars.peak = 30; refreshStats();")
    out = js(page, "ST.dmg")
    run(page, "towerEnter(1, 1); refreshStats();")
    t1 = js(page, "ST.dmg")
    run(page, "S.stars.b.pow = 0; S.stars.peak = 0; refreshStats();")
    assert js(page, "ST.dmg") == t1  # в башне звёзды ни на что не влияют
    run(page, "S.stars.b.pow = 30; S.stars.peak = 30; towerExit(); refreshStats();")
    assert abs(js(page, "ST.dmg") - out) < 1e-6


def test_oni_keeps_stars(page):
    run(page, FULL + " S.stars.b.fury = 7; S.stars.peak = 12; oniAwaken();")
    assert js(page, "S.stars.b.fury") == 7 and js(page, "S.stars.peak") == 12


def test_garbage_sanitized(page, V6):
    load_save(page, {**V6, "stars": {"b": {"pow": -4, "zzz": 3, "vit": "7"}, "spent": "x", "peak": 2}})
    assert js(page, "S.stars.b.pow") == 0 and js(page, "'zzz' in S.stars.b") is False and js(page, "S.stars.b.vit") == 7
    assert js(page, "S.stars.spent") == 0 and js(page, "S.stars.peak") == 7

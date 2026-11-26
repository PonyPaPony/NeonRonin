"""Частокол вдоль выхода из базы: настоящая стена с одними воротами на средней улице; вышки вдоль стены — по числу шагов."""
from conftest import js, run

SETUP = "S.village.crystal = true; S.village.queue = [];"


def steps(page, pal, t1=0, t2=0):
    run(page, SETUP + f"S.village.steps.palisade = {pal}; S.village.steps.tower1 = {t1}; S.village.steps.tower2 = {t2}; vWallObs(); refreshStats();")


def test_no_wall_before_built(page):
    steps(page, 0)
    assert js(page, "pointBlocked(vWallX(), 600, 0)") is False


def test_wall_blocks_outside_gate(page):
    steps(page, 1)
    assert js(page, "pointBlocked(vWallX(), 600, 0)") is True
    assert js(page, "pointBlocked(vWallX(), 2600, 0)") is True
    assert js(page, "pointBlocked(vWallX(), (VWALL.g0 + VWALL.g1) / 2, 0)") is False   # ворота открыты


def test_gate_on_middle_street(page):
    assert js(page, "VWALL.g0 >= 1400 && VWALL.g1 <= 2000 && VWALL.g1 - VWALL.g0 >= 280") is True


def test_hero_cannot_walk_through_wall(page):
    steps(page, 1)
    run(page, "hero.x = vWallX() - 60; hero.y = 700; G.autoHunt = false; window.__keysR = true;")
    page.keyboard.down('d'); page.wait_for_timeout(1500); page.keyboard.up('d')
    assert js(page, "hero.x < vWallX()") is True


def test_hero_cannot_dash_through_wall(page):
    steps(page, 1)
    run(page, "G.speed = 0.25; hero.x = vWallX() - 30; hero.y = 700; hero.dashT = 0.5; hero.dashDx = 1; hero.dashDy = 0;")
    page.wait_for_timeout(1200)
    assert js(page, "hero.x < vWallX()") is True


def test_hero_walks_through_gate(page):
    steps(page, 1)
    run(page, "hero.x = vWallX() - 80; hero.y = (VWALL.g0 + VWALL.g1) / 2;")
    page.keyboard.down('d'); page.wait_for_timeout(1500); page.keyboard.up('d')
    assert js(page, "hero.x > vWallX() + 20") is True


def test_towers_count_follows_steps(page):
    steps(page, 1, 2, 1)
    assert js(page, "vTowersBuilt().length") == 3
    steps(page, 1, 3, 3)
    assert js(page, "vTowersBuilt().length") == 6
    assert js(page, "vTowersBuilt().every(t => Math.abs(t.x - (vWallX() - 65)) < 1)") is True
    assert js(page, "vTowersBuilt().every(t => t.y < VWALL.g0 || t.y - 26 > VWALL.g1)") is True   # вышки не перекрывают ворота


def test_tower_plot_marks_next_site(page):
    steps(page, 1, 1, 0)
    r = js(page, "[VPLOTS.tower1.y, VT_SLOTS.tower1[1][1], VPLOTS.tower2.y, VT_SLOTS.tower2[0][1]]")
    assert r[0] == r[1] and r[2] == r[3]


def test_bonuses_unchanged(page):
    steps(page, 2, 3, 3)
    assert abs(js(page, "vBonus('hp')") - 0.18) < 1e-9
    assert abs(js(page, "vBonus('reduce')") - 0.04) < 1e-9


def test_autohunt_goes_through_gate(page):
    steps(page, 1)
    run(page, "hero.x = 700; hero.y = 700; G.autoAnchor = { x: 1500, y: 700 }; G.autoTarget = null;")
    d = js(page, "(() => { const a = vWallSteer(hero, { x: 1, y: 0, mag: 1 }); return [a.x, a.y]; })()")
    assert d[1] > 0.5        # стена — идём вниз к воротам, а не упираемся


def test_wall_off_in_tower(page):
    steps(page, 3)
    run(page, "runCmd('unlock3'); travelTo(3); runCmd('tower'); towerEnter(0, 1);")
    page.wait_for_function("S.loc === 4", polling=100, timeout=10000)
    assert js(page, "WORLD.obstacles.some(o => o.vWall)") is False


def test_wall_draws_without_errors(page):
    steps(page, 3, 3, 3)
    run(page, "hero.x = vWallX() - 100; hero.y = 1700; G.cam.x = hero.x; G.cam.y = hero.y;")
    page.wait_for_timeout(600)
    assert page.errors == []


def test_all_tower_slots_clear(page):
    bad = js(page, """(() => { const r = [], X = vWallX(); for (const id in VT_SLOTS) VT_SLOTS[id].forEach(([dx, y], i) => { const p = { x: X + dx, y, w: VPLOTS[id].w, h: VPLOTS[id].h };
        const hit = (o, rr) => { const cx = clamp(o.x, p.x - p.w / 2, p.x + p.w / 2), cy = clamp(o.y, p.y - p.h, p.y); return Math.hypot(o.x - cx, o.y - cy) < rr; };
        if ([FORGE, BOARD, SHOP, NURSERY, PORTAL].some(o => hit(o, o.r + 30)) || hit(DUMMY, 70) || hit(SPAWN, 60) || hit(RATUSHA, RATUSHA.r + 20)) r.push(id + i);
        for (const [oid, b] of Object.entries(VPLOTS)) if (!VT_SLOTS[oid] && oid !== 'palisade' && Math.abs(p.x - b.x) < (p.w + b.w) / 2 && p.y - p.h < b.y && b.y - b.h < p.y) r.push(id + i + '/' + oid); }); return r; })()""")
    assert bad == []

"""Руны 2а: исправления по финальному ревью."""
from conftest import js, run

BASE = "runCmd('unlock3'); runCmd('soul 100'); S.tower.unlocked = true; travelTo(3); fixSlots(); S.w.rank = 12; S.w.ench = [null, null, null, null]; refreshStats(); G.speed = 0.0001; S.village.peakGM = 1000; S.gold = 1e15;"
R = "{id:'%s', r:%d, f:[0,0,0,0,0,0]}"


def test_dodge_above_cap_kept_without_runes(page):          # I1
    run(page, BASE)
    assert js(page, "(() => { ST.dodge = 0.55; return runeDodge(); })()") == 0.55
    run(page, f"S.brace.lvl = 1; S.runes.j[1] = {R % ('shade', 5)}; refreshStats();")
    assert js(page, "(() => { ST.dodge = 0.55; G.dodgeBuffT = G.time + 2; return runeDodge(); })()") == 0.55
    assert js(page, "(() => { ST.dodge = 0.4; G.dodgeBuffT = G.time + 2; return runeDodge(); })()") == 0.45


def test_crack_decays_one_per_step_per_frame(page):          # I2
    run(page, BASE + f"S.runes.w[0] = {R % ('pierce', 5)}; refreshStats();")
    r = js(page, """(() => { const d = G.dummy; d.st = null; d.hp = d.maxHp = 1e15; for (let i = 0; i < 10; i++) dealDamage(d, 1); const t0 = G.time, out = {};
      for (let k = 1; k <= 60 * 9.5; k++) { G.time = t0 + k / 60; const n = runeCrackN(d); for (const s of [3.5, 4.55, 6.05, 7.55, 9.05]) if (Math.abs(k / 60 - s) < 1 / 120) out[s] = n; } return out; })()""")
    assert r == {'3.5': 7, '4.55': 6, '6.05': 5, '7.55': 4, '9.05': 3}


def test_breath_triggers_from_dot_tick(page):                # I3
    run(page, BASE + f"S.neck.lvl = 1; S.runes.j[2] = {R % ('heart', 5)}; refreshStats(); G.breathCd = 0;")
    r = js(page, "(() => { const m = ST.maxHp; hero.dead = false; hero.x = 3000; hero.hp = m * 0.31; hero.shield = 0; hero.hpoison = {t: 3, tick: 0, dps: m * 0.04}; updateHeroStatus(0.01); return [hero.hp / m, hero.shield / m]; })()")
    assert r[0] > 0.6 and abs(r[1] - 0.25) < 1e-6


def test_shade_crit_not_spent_by_pet(page):                  # M1
    run(page, BASE + f"S.runes.a[0] = {R % ('shade', 5)}; refreshStats();")
    r = js(page, "(() => { const d = G.dummy; d.eva = 0; d.hp = d.maxHp = 1e15; G.shadeCrit = G.time + 3; dealDamage(d, 10, {src:'pet', small:true, noProc:true, noKb:true}); dealDamage(d, 10, {src:'react', small:true, noProc:true}); return G.shadeCrit > G.time; })()")
    assert r is True


def test_bond_scales_item_mul(page):                         # M2
    run(page, BASE + "S.pets.owned.tanuki = {lvl: 45, xp: 0, picks: [0, 0, 0, 0, 1, null], x2: [null, null, null, null, 0]}; S.pets.active = 'tanuki'; fixPets();" + f"S.ring.lvl = 1; S.runes.j[0] = {R % ('bond', 0)}; refreshPetFx();")
    assert abs(js(page, "PFX.itemMul") - 0.4) < 1e-9


def test_pick_confirm_bound_to_target(page):                 # M3
    run(page, BASE + f"S.runes.w[0] = {R % ('spirit', 2)}; S.runes.frag[2] = 100; G.runeSel = {{item:'w', slot:0}}; openForge(); G.forgeTab = 'r'; renderForge();")
    page.click("#forge [data-act='rrp'][data-id='poison']")
    page.wait_for_timeout(400)
    page.click("#forge [data-act='rrp'][data-id='shade']")
    assert js(page, "S.runes.w[0].id") == 'spirit'


def test_double_tap_upgrade_and_forge(page):                 # M4
    run(page, BASE + f"S.runes.w[0] = {R % ('spirit', 1)}; S.runes.frag = [20, 0, 40, 40, 0, 0]; G.runeSel = {{item:'w', slot:0}}; openForge(); G.forgeTab = 'r'; renderForge();")
    run(page, "for (let i = 0; i < 2; i++) { const b = document.querySelector(\"#forge [data-act='rup']\"); if (b && !b.disabled) b.click(); }")
    assert js(page, "S.runes.w[0].r") == 2
    page.wait_for_timeout(400)
    run(page, "for (let i = 0; i < 2; i++) { const b = document.querySelector(\"#forge [data-act='rforge'][data-slot='0']\"); if (b && !b.disabled) b.click(); }")
    assert js(page, "S.runes.bag.length") == 1 and js(page, "S.runes.frag[0]") == 10


def test_rage_cd_floor_kept(page):                           # M8
    run(page, BASE + "S.neck.lvl = 1; S.oni = true; refreshStats();" + f"S.runes.j[2] = {R % ('time', 5)}; refreshStats(); PFX.superCd = 400;")
    assert js(page, "(() => { S.oniE = 100; S.oniCd = 0; G.oniSuperT = 0; tryOniSuper(); return S.oniCd; })()") == 60

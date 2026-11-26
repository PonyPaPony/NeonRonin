from conftest import js, run, frames, load_save

MK = """(() => { const e = makeDummy(); e.dummy = false; e.type = 'bruiser'; e.hp = e.maxHp = 1e9; e.def = 0; e.eva = 0; e.x = hero.x + 300; e.y = hero.y; e.speed = 100; e.dmg = 0; G.enemies.push(e); window.__e = e; return true; })()"""


def wpn(page, *ench):
    run(page, "S.w.ench = [" + ", ".join(ench) + "]; while (S.w.ench.length < 4) S.w.ench.push(null); refreshStats(); ST.critChance = 0;")


def test_poison_stacks_and_antiheal(page):
    js(page, MK); wpn(page, "{id: 'poison', t: 3, v: 12}")
    run(page, "for (let i = 0; i < 7; i++) dealDamage(__e, 100, {noKb: true});")
    assert js(page, "[__e.st.poison.n, __e.st.poison.dps]") == [5, 12]
    assert js(page, "elemHealMul(__e)") == 0.5
    h0 = js(page, "__e.hp"); run(page, "for (let i = 0; i < 60; i++) elemTick(__e, 1/60);")
    assert abs((h0 - js(page, "__e.hp")) - 5 * 12) < 1e-6


def test_shaman_heal_halved(page):
    js(page, MK); wpn(page, "{id: 'poison', t: 3, v: 12}")
    run(page, "__e.hp = __e.maxHp * 0.5; dealDamage(__e, 100, {noKb: true}); window.__h0 = __e.hp;")
    run(page, "const m = __e; m.healLock = 0; const hv = m.maxHp * 0.14 * elemHealMul(m); window.__exp = window.__h0 + hv;")
    assert js(page, "elemHealMul(__e)") == 0.5


def test_frost_slow_and_freeze(page):
    js(page, MK); wpn(page, "{id: 'frost', t: 3, v: 11}")
    run(page, "for (let i = 0; i < 4; i++) dealDamage(__e, 100, {noKb: true});")
    assert abs(js(page, "elemSlow(__e)") - (1 - 0.32)) < 1e-9 and js(page, "elemFrozen(__e)") is False
    run(page, "dealDamage(__e, 100, {noKb: true});")
    assert js(page, "elemFrozen(__e)") is True
    run(page, "for (let i = 0; i < 70; i++) elemTick(__e, 1/60); for (let i = 0; i < 5; i++) dealDamage(__e, 100, {noKb: true});")
    assert js(page, "elemFrozen(__e)") is False   # повтор не раньше 4 с


def test_boss_never_frozen(page, V6):
    wpn(page, "{id: 'frost', t: 5, v: 22}")
    run(page, "const b = makeBoss(1); b.hp = b.maxHp = 1e12; b.x = hero.x + 300; b.y = hero.y; G.enemies.push(b); window.__b = b; for (let i = 0; i < 10; i++) dealDamage(b, 100, {noKb: true});")
    assert js(page, "elemFrozen(__b)") is False and js(page, "elemSlow(__b)") >= 0.75 - 1e-9


def test_frost_extra_damage(page):
    js(page, MK); wpn(page, "{id: 'frost', t: 3, v: 11}")
    h0 = js(page, "__e.hp"); run(page, "applyElem(__e, 'ice', 100, 'ice');")
    assert abs((h0 - js(page, "__e.hp")) - 11) < 1e-6


def test_dark_bonus_vs_wounded(page):
    js(page, MK)
    assert abs(js(page, "(__e.hp = __e.maxHp * 0.2, darkMul(__e))") - 1.4) < 1e-9
    assert js(page, "(__e.hp = __e.maxHp, darkMul(__e))") == 1


def test_dark_only_for_oni(page):
    js(page, MK)
    run(page, "S.oni = false; refreshStats(); dealDamage(__e, 100, {noKb: true}); window.__a = !!(__e.st && __e.st.shadow);")
    run(page, "S.oni = true; refreshStats(); applyElem(__e, 'dark', 45, 'oni');")
    assert js(page, "window.__a") is False and js(page, "__e.st.shadow.t > 1.9") is True


def test_new_enchants_roll(page):
    for k in ('poison', 'frost'):
        r = js(page, f"rollEnch('{k}')")
        assert r["id"] == k and 1 <= r["t"] <= 5 and r["v"] > 0
    assert js(page, "ENCH.poison.slot") == 'w' and js(page, "ENCH.frost.slot") == 'w'
    assert js(page, "ENCH.poison.el") == 'poison' and js(page, "ENCH.frost.el") == 'ice'


def test_tower_mob_freezes_guard_does_not(page):
    wpn(page, "{id: 'frost', t: 3, v: 11}")
    run(page, "const a = makeTowerMob('bruiser', hero.x + 300, hero.y, false); a.hp = a.maxHp = 1e9; a.def = 0; a.eva = 0; G.enemies.push(a); window.__a = a;"
              "const g = makeTowerMob('bruiser', hero.x + 300, hero.y + 40, true); g.mini = true; g.hp = g.maxHp = 1e9; g.def = 0; g.eva = 0; G.enemies.push(g); window.__g = g;"
              "for (let i = 0; i < 5; i++) { dealDamage(__a, 100, {noKb: true}); dealDamage(__g, 100, {noKb: true}); }")
    assert js(page, "elemFrozen(__a)") is True
    assert js(page, "elemFrozen(__g)") is False and js(page, "elemSlow(__g)") >= 0.75 - 1e-9

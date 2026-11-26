from conftest import js, run

MK = """(() => { const e = makeDummy(); e.dummy = false; e.type = 'bruiser'; e.hp = e.maxHp = 1e12; e.def = 0; e.eva = 0; e.x = hero.x + 300; e.y = hero.y; e.speed = 0; e.dmg = 0; G.enemies.push(e); window.__e = e; return true; })()"""


def test_eclipse_does_not_grow_without_limit(page):
    js(page, MK)
    run(page, "S.oni = true; S.w.ench = [{id:'burn',t:4,v:24}, null, null, null]; refreshStats(); ST.critChance = 0;"
              "for (let s = 0; s < 20; s++) { for (let i = 0; i < 3; i++) { dealDamage(__e, 100, {noKb: true}); applyElem(__e, 'dark', 45, 'oni'); } __e.st.rcd.eclipse = 0; }")
    eff = js(page, "fireDpsNow(__e)")
    assert eff <= 24 * 1.5 + 1e-6


def test_elem_dmg_respects_aura_mountain_armor(page):
    js(page, MK)
    h0 = js(page, "__e.hp"); run(page, "__e.tArm = 0.75; elemDmg(__e, 'fire', 100, 'fire');")
    assert abs((h0 - js(page, "__e.hp")) - 75) < 1e-6
    run(page, "runCmd('unlock3'); travelTo(3);"); js(page, MK)
    assert js(page, "mountainWeak()") is True
    h1 = js(page, "__e.hp"); run(page, "elemDmg(__e, 'poison', 100, 'poison');")
    assert abs((h1 - js(page, "__e.hp")) - 60) < 1e-6


def test_pet_burn_does_not_stack(page):
    js(page, MK)
    run(page, "for (let i = 0; i < 5; i++) applyElem(__e, 'fire', 0, 'pet', { dps: 50, pet: true });")
    assert js(page, "__e.st.fire.n") == 1

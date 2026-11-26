from conftest import js, run, frames, load_save

MK = """(() => { const e = makeDummy(); e.dummy = false; e.type = 'bruiser'; e.hp = e.maxHp = 1e9; e.def = 0; e.eva = 0; e.x = hero.x + 300; e.y = hero.y; e.speed = 0; e.dmg = 0; G.enemies.push(e); window.__e = e; return true; })()"""
W = "S.w.ench = [{id: 'burn', t: 3, v: 16}, null, null, null]; refreshStats();"


def test_fire_stacks_and_ticks(page):
    js(page, MK); run(page, W + " ST.critChance = 0; for (let i = 0; i < 3; i++) dealDamage(__e, 100, {noKb: true});")
    assert js(page, "__e.st.fire.n") == 3
    h0 = js(page, "__e.hp"); run(page, "for (let i = 0; i < 60; i++) elemTick(__e, 1/60);")
    d = h0 - js(page, "__e.hp")
    assert abs(d - 3 * 0.16 * 100) / (3 * 16) < 0.12


def test_fire_from_precrit_base(page):
    js(page, MK)
    run(page, W + " ST.critChance = 1; ST.critDmg = 3; dealDamage(__e, 100, {noKb: true});")
    assert abs(js(page, "__e.st.fire.dps") - 16) < 1e-6


def test_fire_can_crit(page):
    js(page, MK); run(page, W + " ST.critChance = 0; dealDamage(__e, 100, {noKb: true}); ST.critChance = 1; ST.critDmg = 2;")
    h0 = js(page, "__e.hp"); run(page, "for (let i = 0; i < 30; i++) elemTick(__e, 1/60);")
    assert abs((h0 - js(page, "__e.hp")) - 16 * 0.5 * 2) < 1e-6


def test_same_element_half(page):
    js(page, MK); run(page, "__e.elem = 'fire';")
    h0 = js(page, "__e.hp"); run(page, "elemDmg(__e, 'fire', 100, 'fire');")
    assert abs((h0 - js(page, "__e.hp")) - 50) < 1e-6
    h1 = js(page, "__e.hp"); run(page, "elemDmg(__e, 'ice', 100, 'ice');")
    assert abs((h1 - js(page, "__e.hp")) - 100) < 1e-6


def test_fire_spread_on_death(page):
    for _ in range(4): js(page, MK)
    run(page, "const L = G.enemies.filter(x => x.hp === 1e9).slice(-4); L.forEach((x, i) => { x.x = hero.x + 300 + i * 40; }); window.__L = L;")
    run(page, W + " ST.critChance = 0; for (let i = 0; i < 4; i++) dealDamage(__L[0], 100, {noKb: true}); __L[0].hp = 1; killEnemy(__L[0]);")
    assert js(page, "__L.slice(1).filter(x => x.st && x.st.fire && x.st.fire.n === 4).length") == 2


def test_thunder_sets_zap_and_stun(page):
    js(page, MK); js(page, MK)
    run(page, "const L = G.enemies.filter(x => x.hp === 1e9).slice(-2); L[1].x = L[0].x + 50; window.__L = L; const r = Math.random; Math.random = () => 0; chainLightning(L[0], 2, 100); Math.random = r;")
    z, st = js(page, "[__L[1].st.zap.t, __L[1].st.stun.t]")
    assert abs(z - 2) < 0.05 and abs(st - 0.4) < 0.05
    run(page, "const b = makeBoss(1); b.x = __L[0].x + 60; b.y = __L[0].y; G.enemies.push(b); window.__b = b; const r = Math.random; Math.random = () => 0; chainLightning(__L[0], 3, 100); chainLightning(__L[0], 3, 100); Math.random = r;")
    assert abs(js(page, "__b.st.stun.t") - 0.1) < 0.05
    assert js(page, "__b.st.stun.cd > G.time + 2.5") is True


def test_pet_burn_uses_fire_stacks(page):
    js(page, MK); run(page, "applyElem(__e, 'fire', 0, 'pet', { dps: 50 });")
    assert js(page, "[__e.st.fire.n, __e.st.fire.dps]") == [1, 50]
    assert js(page, "typeof __e.burnDps === 'undefined' || !__e.burnDps") is True


def test_burn_migration(page, V6):
    for v, t, exp in [(90, 5, 36), (45, 3, 18)]:
        d = dict(V6); w = dict(d['w']); w['ench'] = [{'id': 'burn', 't': t, 'v': v}, None, None, None]; d['w'] = w; d.pop('elemMig', None)
        load_save(page, d)
        assert js(page, "S.w.ench[0].v") == exp
        run(page, "fixSlots();")
        assert js(page, "S.w.ench[0].v") == exp


def test_dps_meter_fire_source(page):
    assert js(page, "DPS_SRC.fire[0]") == "Огонь"

from conftest import js, run

MK = """(() => { const e = makeDummy(); e.dummy = false; e.type = 'bruiser'; e.hp = e.maxHp = 1e9; e.def = 0; e.eva = 0; e.x = hero.x + 300 + G.enemies.length * 30; e.y = hero.y; e.speed = 0; e.dmg = 0; G.enemies.push(e); window.__e = e; return true; })()"""


def wpn(page, *ench):
    run(page, "S.w.ench = [" + ", ".join(ench) + "]; while (S.w.ench.length < 4) S.w.ench.push(null); refreshStats(); ST.critChance = 0;")


def test_smoke_reduces_def(page):
    js(page, MK); wpn(page, "{id: 'burn', t: 3, v: 16}", "{id: 'poison', t: 3, v: 12}")
    run(page, "__e.def = 0.5; ST.pen = 0; dealDamage(__e, 100, {noKb: true});")
    assert abs(js(page, "__e.st.smoke.t") - 6) < 0.05
    assert js(page, "G.lastReact") == "Едкий дым"


def test_steam_aoe_and_clears_ice(page):
    js(page, MK); js(page, MK); run(page, "window.__o = G.enemies[G.enemies.length - 2];")
    wpn(page, "{id: 'frost', t: 3, v: 11}")
    run(page, "for (let i = 0; i < 2; i++) dealDamage(__e, 100, {noKb: true});")
    h_other = js(page, "__o.hp")
    run(page, "applyElem(__e, 'fire', 100, 'fire', {dps: 1});")
    assert js(page, "G.lastReact") == "Пар"
    assert js(page, "__e.st.ice.n") == 0 and js(page, "__o.hp") < h_other


def test_spark_doubles_chain(page):
    js(page, MK); js(page, MK); run(page, "G.enemies = G.enemies.slice(-2); window.__o = G.enemies[0];")   # только свои две цели: случайный моб мира не перехватит молнию
    run(page, "applyElem(__o, 'ice', 0, 'ice'); applyElem(__o, 'thunder', 0, 'chain');")
    assert js(page, "G.lastReact") == "Ледяная искра" and abs(js(page, "__o.st.spark.t") - 3) < 0.2
    h0 = js(page, "__o.hp"); run(page, "const r = Math.random; Math.random = () => 0.5; chainLightning(__e, 1, 100); Math.random = r;")
    assert (h0 - js(page, "__o.hp")) > 150


def test_toxic_spreads_and_bursts(page):
    for _ in range(3): js(page, MK)
    run(page, "window.__L = G.enemies.filter(x => x.hp === 1e9).slice(-3); applyElem(__L[0], 'poison', 0, 'poison', {dps: 10, n: 3});")
    rem = js(page, "__L[0].st.poison.n * __L[0].st.poison.dps * __L[0].st.poison.t")
    run(page, "const r = Math.random; Math.random = () => 0.5; chainLightning(__L[0], 2, 1); Math.random = r;")
    assert js(page, "__L.filter(x => x.st && x.st.pb && x.st.pb.t > 0 && x.st.pb.t <= 1.0001).length") == 3
    assert abs(js(page, "__L[1].st.pb.dmg") - 2 * 10 * 4) < 1.5
    h0 = js(page, "__L[0].hp"); run(page, "for (let i = 0; i < 63; i++) elemTick(__L[0], 1/60);")
    assert abs((h0 - js(page, "__L[0].hp")) - rem) / rem < 0.05


def test_eclipse_only_oni(page):
    js(page, MK)
    run(page, "S.oni = false; applyElem(__e, 'fire', 0, 'fire', {dps: 10}); applyElem(__e, 'dark', 0, 'oni');")
    assert js(page, "__e.st.fire.dps") == 10
    run(page, "S.oni = true; __e.st.rcd = {}; applyElem(__e, 'dark', 0, 'oni');")
    assert js(page, "fireDpsNow(__e)") == 15 and js(page, "G.lastReact") == "Затмение"


def test_reaction_cooldown_per_type(page):
    js(page, MK)
    run(page, "applyElem(__e, 'fire', 0, 'fire', {dps: 1}); applyElem(__e, 'poison', 0, 'poison', {dps: 1}); G.lastReact = null; applyElem(__e, 'poison', 0, 'poison', {dps: 1});")
    assert js(page, "G.lastReact") is None
    run(page, "applyElem(__e, 'thunder', 0, 'chain');")
    assert js(page, "G.lastReact") == "Токсичный разряд"


def test_reaction_popup_text(page):
    js(page, MK)
    run(page, "applyElem(__e, 'fire', 0, 'fire', {dps: 1}); applyElem(__e, 'poison', 0, 'poison', {dps: 1});")
    assert js(page, "G.texts.some(t => t.txt === 'Едкий дым!')") is True


def test_forge_shows_combos(page):
    assert "Сочетается с" in js(page, "ENCH.poison.fmt({v: 12, t: 3})")
    assert "Сочетается с" in js(page, "ENCH.burn.fmt({v: 16, t: 3})")


def test_toxic_burst_does_not_inflate_later_poison(page):
    js(page, MK)
    run(page, "applyElem(__e, 'poison', 0, 'poison', {dps: 10, n: 3}); vToxicBurst(__e); applyElem(__e, 'poison', 0, 'poison', {dps: 10});")
    assert js(page, "__e.st.poison.dps") == 10

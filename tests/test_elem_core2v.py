"""Этап 2в: стихийная основа — перевод Волны/Вихря, метки реакций, «Всплеск стихий»."""
from conftest import js, run

E = {'burn': "{id: 'burn', t: 5, v: 52.6}", 'frost': "{id: 'frost', t: 5, v: 40.9}", 'chain': "{id: 'chain', t: 5, v: 43.8}",
     'poison': "{id: 'poison', t: 5, v: 46.7}", 'crit': "{id: 'crit', t: 5, v: 32.1, v2: 146}", 'vamp': "{id: 'vamp', t: 5, v: 14.6}"}
BASE = ("runCmd('открыть всё'); runCmd('soul 100'); travelTo(3); fixSlots(); S.w.rank = 12; S.w.ench = [null, null, null, null]; S.ring.lvl = S.brace.lvl = S.neck.lvl = 1;"
        "window.put = (k, ids, r) => { S.runes[k] = ids.map(id => id ? {id, r: r === undefined ? 5 : r, f: [0,0,0,0,0,0]} : null); refreshPetFx(); refreshStats(); };"
        "window.ench = ids => { S.w.ench = ids.map(i => i ? eval('(' + ({%s})[i] + ')') : null); refreshStats(); };"
        "refreshStats(); G.speed = 0.0001;") % ", ".join(f"{k}: \"{v}\"" for k, v in E.items())
MOBS = ("const mk = (dx, dy, el) => { const e = makeEnemy('bruiser', hero.x + dx, hero.y + dy, 1, false); e.hp = e.maxHp = 1e15; e.def = 0; e.eva = 0; e.elem = el || null; G.enemies.push(e); return e; };"
        "G.enemies.length = 0; Math.random = () => 0.5; ST.critChance = 0; ST.chain = 0; ST.execute = 0;")
SPY = "const log = []; const dd = dealDamage; window.dealDamage = (e, b, o) => { log.push([(o && o.src) || 'katana', (o && o.el) || null, b]); return dd(e, b, o); };"
UNSPY = "window.dealDamage = dd;"


def split(page):
    return js(page, "(() => { const s = ST.split; return [+(s.fire || 0).toFixed(4), +(s.thunder || 0).toFixed(4), +(s.ice || 0).toFixed(4), +(s.poison || 0).toFixed(4), +s.sum.toFixed(4)]; })()")


# ---------- Task 1: перевод Волны и Вихря ----------
def test_split_needs_two(page):
    run(page, BASE + "ench(['chain', 'crit', 'vamp', null]);")
    assert split(page)[4] == 0                                       # одна стихийная чара — перевода нет (Кирин)
    r = js(page, "(() => { " + MOBS + SPY + " const a = mk(40, 0); hero.swingCount = 3; heroAttack(a); " + UNSPY + " return log.filter(x => x[0].startsWith('whirl')); })()")
    assert len(r) == 1 and r[0][1] is None                           # вихрь — один физический удар, как раньше


def test_split_shares(page):
    run(page, BASE + "ench(['burn', 'frost', null, null]);")
    assert split(page) == [0.2, 0, 0.2, 0, 0.4]
    run(page, "ench(['burn', 'frost', 'chain', null]);")
    assert split(page) == [0.2, 0.2, 0.2, 0, 0.6]
    run(page, "ench(['burn', 'frost', 'chain', 'poison']);")
    assert split(page) == [0.2, 0.2, 0.2, 0.2, 0.8]


def test_split_hits(page):
    run(page, BASE + "ench(['burn', 'frost', 'crit', null]);")
    r = js(page, "(() => { " + MOBS + SPY + " const a = mk(40, 0); hero.swingCount = 3; heroAttack(a); " + UNSPY + " return log.filter(x => x[0].startsWith('whirl')).map(x => [x[0], x[1], x[2] / (ST.dmg * 1.3 * ST.skillMul)]); })()")
    got = sorted((s, el, round(k, 4)) for s, el, k in r if el)
    assert got == [('whirl_el', 'fire', 0.2), ('whirl_el', 'ice', 0.2)]
    phys = [round(k, 4) for s, el, k in r if not el and s == 'whirl']
    assert phys == [1.0, 0.6]                                      # вход (полный удар) → физ. часть 60%
    # Волна
    r = js(page, "(() => { " + MOBS + SPY + " const a = mk(60, 0); G.waves.length = 0; hero.swingCount = 1; hero.face = 1; heroAttack(a); for (let i = 0; i < 20; i++) updateProjectiles(0.016); " + UNSPY + " return log.filter(x => x[0].startsWith('wave')).map(x => [x[0], x[1]]); })()")
    assert ['wave', None] in r and ['wave_el', 'fire'] in r and ['wave_el', 'ice'] in r


def test_split_one_text(page):
    run(page, BASE + "ench(['burn', 'frost', 'crit', null]);")
    r = js(page, "(() => { " + MOBS + " const a = mk(40, 0); G.texts.length = 0; dealDamage(a, 1000, {src: 'whirl', noKb: true, noProc: true}); return G.texts.length; })()")
    assert r == 1                                                     # одна надпись на удар


def test_split_obeys_elem_rules(page):
    run(page, BASE + "ench(['burn', 'frost', 'crit', null]);")
    r = js(page, "(() => { " + MOBS + " const a = mk(40, 0, 'fire'), b = mk(40, 40, 'thunder'); a.def = b.def = 0.4; ST.pen = 0;"
                 " dealDamage(a, 1000, {src: 'whirl', noKb: true, noProc: true}); dealDamage(b, 1000, {src: 'whirl', noKb: true, noProc: true});"
                 " return [(1e15 - a.hp), (1e15 - b.hp), physMul({src: 'whirl'})]; })()")
    pm = r[2]
    # физ. часть: 600 × (1 − 0,4) × physMul; стихийная: 200 × (1 − 0,2) (половина защиты), огонь по огненному — ×0,5
    assert abs(r[0] - (600 * 0.6 * pm + 200 * 0.8 * 0.5 + 200 * 0.8)) < 1e-3 * r[0]
    assert abs(r[1] - (600 * 0.6 * pm + 200 * 0.8 + 200 * 0.8)) < 1e-3 * r[1]


def test_split_storm(page):
    run(page, BASE + "ench(['burn', 'frost', 'chain', 'poison']); put('w', ['elem', 'elem', 'elem']);")
    s = split(page)
    assert abs(s[0] - (0.2 + 0.2 / 3)) < 1e-3 and abs(s[2] - (0.2 + 0.2 / 3)) < 1e-3 and s[3] == 0.2 and abs(s[4] - 1) < 1e-6
    run(page, "ench([null, null, 'crit', null]);")
    s = split(page)
    assert abs(s[0] - 0.2 / 3) < 1e-3 and abs(s[1] - 0.2 / 3) < 1e-3 and abs(s[2] - 0.2 / 3) < 1e-3 and abs(s[4] - 0.2) < 1e-6   # без чар — поровну


def test_shadow_dance_stays_phys(page):
    run(page, BASE + "ench(['burn', 'frost', 'chain', 'poison']);")
    r = js(page, "(() => { " + MOBS + SPY + " const a = mk(40, 0), b = mk(80, 0); shadowDance(a); " + UNSPY + " return log.filter(x => x[1]).length; })()")
    assert r == 0


# ---------- Task 2: метки реакций ----------
REACT_LOOP = "const react = (e, n) => { for (let i = 0; i < n; i++) { e.st = e.st || {rcd: {}}; e.st.rcd = {}; e.st.fire = null; e.st.poison = null; applyElem(e, 'fire', 100, 'fire'); applyElem(e, 'poison', 100, 'poison'); } };"


def test_rmarks_boss_only_cap(page):
    run(page, BASE + "ench(['burn', 'poison', null, null]);")
    r = js(page, "(() => { " + MOBS + REACT_LOOP + " const b = mk(40, 0), m = mk(80, 0); b.boss = true; react(b, 20); react(m, 3); return [b.st.rm && b.st.rm.n, m.st.rm ? m.st.rm.n : 0]; })()")
    assert r == [12, 0]                                              # до 12 и только на боссах/стражах


def test_rmarks_decay(page):
    run(page, BASE)
    r = js(page, "(() => { " + MOBS + " const b = mk(40, 0); b.mini = true; eSt(b).rm = {n: 5, t: G.time - 4.5}; elemTick(b, 0.016); const a = b.st.rm.n; elemTick(b, 0.016); const c = b.st.rm.n; G.time += 1.01; elemTick(b, 0.016); return [a, c, b.st.rm.n]; })()")
    assert r == [4, 4, 3]                                            # через 4 с без реакций — по одной в секунду


def test_rmarks_boost_elem_only(page):
    run(page, BASE)
    r = js(page, "(() => { " + MOBS + " const b = mk(40, 0); b.boss = true; eSt(b).rm = {n: 10, t: G.time};"
                 " const e1 = elemDmg(b, 'fire', 100, 'fire'); let h = b.hp; dealDamage(b, 100, {noKb: true, noProc: true}); const ph = h - b.hp;"
                 " h = b.hp; dealDamage(b, 100, {noKb: true, noProc: true, el: 'thunder', src: 'chain', noCrit: true}); return [e1, ph / physMul({}), h - b.hp]; })()")
    assert abs(r[0] - 150) < 1e-6 and abs(r[1] - 100) < 1e-6 and abs(r[2] - 150) < 1e-6


def test_crown_double_marks(page):
    run(page, BASE + "put('j', ['elem', 'elem', 'elem']);")
    r = js(page, "(() => { " + MOBS + REACT_LOOP + " const b = mk(40, 0); b.boss = true; react(b, 1); return b.st.rm.n; })()")
    assert r == 2


# ---------- Task 3: «Всплеск стихий» ----------
SURGE = "S.ring.ench = [{id: 'surge', t: 5, v: 22, v2: 25}, null, null, null]; refreshStats();"
NOSURGE = "S.ring.ench = [null, null, null, null]; refreshStats();"


def test_surge_stat_and_crit(page):
    run(page, BASE + SURGE)
    assert abs(js(page, "ST.surge") - 0.22) < 1e-9 and abs(js(page, "ST.surgeCd") - 0.25) < 1e-9
    hit = "(() => { " + MOBS + " Math.random = () => 0.01; ST.critChance = 0.5; const a = mk(40, 0); chainLightning(a, 4, 1000); return 1e15 - a.hp; })()"
    with_s = js(page, hit)
    run(page, NOSURGE)
    no_s = js(page, hit)
    k = js(page, "ST.critDmg")
    assert abs(with_s / no_s - (k + 0.25) * 1.22) < 1e-3              # со «Всплеском» молния критует: (крит + 25%) × (1 + 22%)


def test_surge_no_tick_crit(page):
    run(page, BASE + SURGE)
    r = js(page, "(() => { " + MOBS + " Math.random = () => 0; ST.critChance = 1; const a = mk(40, 0); eSt(a).poison = {n: 2, t: 4, dps: 100, tick: 0}; const h = a.hp; elemTick(a, 0.016); return h - a.hp; })()")
    assert abs(r - 2 * 100 * 0.5 * 1.22) < 1e-6                       # тик яда: +22%, без крита


def test_surge_not_on_phys(page):
    run(page, BASE + SURGE)
    hit = "(() => { " + MOBS + " const a = mk(40, 0); dealDamage(a, 1000, {noKb: true, noProc: true}); return 1e15 - a.hp; })()"
    a = js(page, hit)
    run(page, NOSURGE)
    assert abs(js(page, hit) - a) < 1e-6


def test_surge_split_parts_crit(page):
    run(page, BASE + "ench(['burn', 'frost', null, null]);" + SURGE)
    r = js(page, "(() => { " + MOBS + " Math.random = () => 0.01; ST.critChance = 0.5; const a = mk(40, 0); G.dsess = null; dealDamage(a, 1000, {src: 'whirl', noKb: true, noProc: true}); return [1e15 - a.hp, ST.critDmg, physMul({src: 'whirl'})]; })()")
    exp = 1000 * 0.902 * (0.6 * r[1] * r[2] + 0.4 * (r[1] + 0.25) * 1.22)
    assert abs(r[0] - exp) < 1e-3 * exp


def test_surge_in_forge_list(page):
    run(page, BASE + SURGE + "fixSlots();")
    assert js(page, "[ENCH.surge.slot, ENCH.surge.name, !!S.ring.ench[0]]") == ['j', 'Всплеск стихий', True]


def test_crown_atk_floor(page):
    run(page, BASE + "put('j', ['elem', 'elem', 'elem']);")
    assert js(page, "(() => { ST.atkCd = 0.16; G.crownT = G.time + 3; return runeAtkCd(); })()") == 0.16


# ---------- Task 5: отладочный модификатор «физ. урон» ----------
def test_physmod(page):
    run(page, BASE + "ench(['burn', 'frost', null, null]);")
    r = js(page, "(() => { " + MOBS + " const a = mk(40, 0), b = mk(80, 0); runCmd('physmod 0.1'); dealDamage(a, 1000, {noKb: true, noProc: true}); dealDamage(b, 1000, {noKb: true, noProc: true, el: 'fire', src: 'chain'}); const pa = 1e15 - a.hp, pb = 1e15 - b.hp; runCmd('physmod 1'); a.hp = b.hp = 1e15; dealDamage(a, 1000, {noKb: true, noProc: true}); dealDamage(b, 1000, {noKb: true, noProc: true, el: 'fire', src: 'chain'}); return [pa / (1e15 - a.hp), pb / (1e15 - b.hp), G.physMod]; })()")
    assert abs(r[0] - 0.1) < 1e-6 and abs(r[1] - 1) < 1e-6 and r[2] == 1


# ---------- финальное ревью 2в ----------
def test_review_crack_once_per_split_hit(page):
    run(page, BASE + "ench(['burn', 'frost', 'chain', 'poison']); put('w', ['pierce', null, null]);")
    r = js(page, "(() => { " + MOBS + " const a = mk(40, 0), b = mk(80, 0); dealDamage(a, 1000, {src: 'katana', noKb: true}); dealDamage(b, 1000, {src: 'whirl', noKb: true}); return [a.st.cr.n, b.st.cr.n]; })()")
    assert r[0] == r[1]                                               # стихийные части не добавляют «Раскол» сверх обычного удара


def test_review_procs_when_parts_kill(page):
    run(page, BASE + "ench(['burn', 'frost', 'chain', 'poison']);")
    r = js(page, "(() => { " + MOBS + " ST.vamp = 0.5; const a = mk(40, 0); a.hp = a.maxHp = 500; hero.hp = 1; G.texts.length = 0; dealDamage(a, 1000, {src: 'whirl', noKb: true}); return [a.dead, hero.hp > 1, G.texts.length >= 1]; })()")
    assert r == [True, True, True]                                   # вампиризм и надпись — даже если стихийные части добили цель


def test_review_vamp_from_full_hit(page):
    run(page, BASE + "ench(['burn', 'frost', 'chain', 'poison']); put('w', ['elem', 'elem', 'elem']);")
    r = js(page, "(() => { " + MOBS + " ST.vamp = 0.001; const a = mk(40, 0); hero.hp = 1; const h = 1e15; dealDamage(a, 1000, {src: 'whirl', noKb: true}); return [hero.hp - 1, (h - a.hp) * 0.001]; })()")
    assert r[0] > 0                                                   # Буря + 4 чары: весь удар стихийный, вампиризм всё равно есть


def test_review_sharp_spirit_not_on_elem_crits(page):
    run(page, BASE + "ench(['burn', 'frost', null, null]); S.brace.lvl = 15; S.brace.ench = [{id: 'sharp', t: 5, v: 22, v2: 50}];" + SURGE + " put('w', ['spirit', null, null]);")
    r = js(page, "(() => { " + MOBS + " Math.random = () => 0.01; ST.critChance = 0.5; const a = mk(40, 0); chainLightning(a, 4, 1000); return [(1e15 - a.hp) / (1000 * 0.902), ST.critDmg]; })()")
    assert abs(r[0] - (r[1] - 0.5 + 0.25) * 1.22) < 1e-3              # «Острота» (+50%) не идёт в стихийный крит


def test_review_oni_dark_no_surge(page):
    run(page, BASE + SURGE)
    r = js(page, "(() => { " + MOBS + " const a = mk(40, 0), b = mk(80, 0); dealDamage(a, 1000, {noKb: true, noProc: true, el: 'dark', src: 'oni', noCrit: true}); " + NOSURGE + " dealDamage(b, 1000, {noKb: true, noProc: true, el: 'dark', src: 'oni', noCrit: true}); return (1e15 - a.hp) / (1e15 - b.hp); })()")
    assert abs(r - 1) < 1e-9                                          # клинок Они (тьма) — не «стихийный урон героини»


def test_review_zamer_counts_split_as_elem(page):
    run(page, BASE + "ench(['burn', 'frost', 'chain', 'poison']); put('w', ['elem', 'elem', 'elem']);")
    r = js(page, "(() => { " + MOBS + " const a = mk(40, 0); zamerStart(); dealDamage(a, 1000, {src: 'whirl', noKb: true, noProc: true}); return G.zm.el / Object.values(G.zm.src).reduce((x, y) => x + y, 0); })()")
    assert r > 0.99


def test_review_pack_in_tower_arena(page):
    run(page, BASE + "S.pets.owned.cat = {lvl: 20, xp: 0, picks: []}; S.pets.active = 'cat'; spawnPetEntity(); put('w', ['bond', 'shade', 'time']);")
    r = js(page, "(() => { const L = S.loc; S.loc = 4; G.pet.x = TW.AX1 - 30; G.pet.y = TW.CY; runePack(1, 0); const x = G.pet.x; S.loc = L; return x <= TW.AX1 - 20; })()")
    assert r is True

"""Руны 2б: сочетания (тройки внутри предмета)."""
from conftest import js, run

BASE = ("runCmd('открыть всё'); runCmd('soul 100'); travelTo(3); fixSlots(); S.w.rank = 12; S.w.ench = [null, null, null, null]; S.ring.lvl = S.brace.lvl = S.neck.lvl = 1;"
        "window.put = (k, ids, r) => { S.runes[k] = ids.map(id => id ? {id, r: r === undefined ? 5 : r, f: [0,0,0,0,0,0]} : null); refreshPetFx(); refreshStats(); };"
        "refreshStats(); G.speed = 0.0001;")


# ---------- Task 1: ядро ----------
def test_combo_detect_and_rank(page):
    run(page, BASE + "put('w', ['shade', 'spirit', 'pierce']);")
    assert js(page, "comboR('ronin')") == 5 and js(page, "ST.ru.rc.ronin") == 5
    run(page, "S.runes.w[1].r = 2; refreshStats();")
    assert js(page, "comboR('ronin')") == 2                        # сила — по слабейшей руне
    run(page, "put('w', ['elem', 'elem', 'elem']);")
    assert js(page, "comboR('storm')") == 5 and js(page, "comboR('ronin')") == -1
    run(page, "put('j', ['time', 'elem', 'bond']);")                 # Стихия в браслете = гром → «Звёздный союз»
    assert js(page, "comboR('union')") == 5
    run(page, "S.brace.lvl = 0; refreshStats();")
    assert js(page, "comboR('union')") == -1                        # руна в несозданном украшении не считается
    assert js(page, "RCOMBO.length") == 20


def test_wrong_slot_hint(page):
    run(page, BASE + "put('w', ['spirit', 'elem', 'pierce']);")        # Стихия во 2-м слоте (гром) → Явление Кирина
    assert js(page, "comboR('kirin')") == 5 and js(page, "comboR('shatter')") == -1
    run(page, "put('w', ['elem', 'spirit', 'pierce']);")             # Стихия в огненном слоте — ни Кирина, ни Ледяного раскола
    assert js(page, "comboR('kirin')") == -1 and js(page, "comboR('shatter')") == -1
    h = js(page, "runeComboHints('w').join(' | ')")
    assert 'Явление Кирина' in h and 'громовом' in h


def test_combo_hints_ui(page):
    run(page, BASE + "put('w', ['spirit', 'shade', null]); S.gold = 1e15; G.runeSel = {item:'w', slot:0}; openForge(); G.forgeTab = 'r'; renderForge();")
    t = page.inner_text('#rune-combo-w')
    assert 'Путь ронина' in t and 'Пробой' in t and 'не хватает' in t
    assert 'Сочетания' in page.inner_text('#f-right .itemcard')
    run(page, "put('w', ['spirit', 'shade', 'pierce']); renderForge();")
    assert '✦ Путь ронина' in page.inner_text('#rune-combo-w')


def test_console_combo_set(page):
    run(page, BASE + "runCmd('combo withyou');")
    assert js(page, "comboR('withyou')") == 5 and js(page, "S.runes.a.every(x => x && x.r === 5)") is True
    run(page, "SET.console = true; toggleConsole(true);")
    assert js(page, "document.querySelectorAll(\"#console [data-cmd^='combo ']\").length") == 20


def test_combos_off_in_tower(page):
    run(page, BASE + "S.tower.charges = 2; put('w', ['shade', 'spirit', 'pierce']);")
    assert js(page, "ST.ru.rc.ronin") == 5
    run(page, "towerEnter(1, 1);")
    assert js(page, "(ST.ru.rc || {}).ronin === undefined && comboR('ronin') === -1") is True


# ---------- Task 2: катана ----------
DUMMY = "const d = G.dummy; G.enemies = [d]; d.hp = d.maxHp = 1e15; d.eva = 0; d.def = 0; d.st = null; G.dsess = null;"
MOBS = """const mk = (dx, dy) => { const e = makeEnemy('bruiser', hero.x + dx, hero.y + dy, 1, false); e.hp = e.maxHp = 1e15; e.eva = 0; e.def = 0; G.enemies.push(e); return e; };"""


def test_storm(page):
    run(page, BASE + "put('w', ['elem', 'elem', 'elem']);")
    assert abs(js(page, "ST.elV.fire") - 0.24 * 0.6) < 1e-9 and abs(js(page, "ST.elV.ice") - 0.20 * 0.6) < 1e-9
    assert abs(js(page, "ST.ru.zapChance") - 0.16 * 0.6) < 1e-9          # без стихийных чар — ×0,6
    r = js(page, "(() => { " + DUMMY + " applyElem(d, 'fire', 100, 'fire'); applyElem(d, 'ice', 100, 'ice'); return d.st.rcd.steam - G.time; })()")
    assert abs(r - 1) < 1e-6                                        # перезарядка реакций на цели 1 с


def test_storm_enchants_soften_penalty(page):
    E = "{id: '%s', t: 5, v: 1}"
    for ench, k in [([], 0.6), (['burn', 'crit'], 0.7), (['burn', 'frost'], 0.8), (['burn', 'frost', 'chain'], 0.9), (['burn', 'frost', 'chain', 'poison'], 1.0)]:
        run(page, BASE + "S.w.ench = [" + ", ".join(E % x for x in ench) + "]; put('w', ['elem', 'elem', 'elem']);")
        assert abs(js(page, "ST.ru.zapChance") - 0.16 * k) < 1e-9, ench   # каждая стихийная чара катаны −0,1 штрафа


def test_ronin(page):
    run(page, BASE + "put('w', ['spirit', 'shade', 'pierce']); Math.random = () => 0.5;")
    r = js(page, "(() => { ST.critChance = 0; hero.shadowCd = 999; G.enemies.length = 0; " + MOBS + " const e = mk(60, 0); tryDash({x: 1, y: 0, mag: 1}); runeShadeStep(hero.x, hero.y, hero.x + 100, hero.y); return [1e15 - e.hp, ST.dmg * ST.skillMul * 2 * ST.critDmg * physMul({src:'shade'}), e.st.cr.n]; })()")
    assert abs(r[0] / r[1] - 1) < 0.01 and r[2] == 3


def test_kirin(page):
    run(page, BASE + "S.w.ench[0] = {id:'chain', t:5, v:43.8}; put('w', ['spirit', 'elem', 'pierce']); Math.random = () => 0;")
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(30, 0), b = mk(90, 0), c = mk(150, 0); const cr = []; const sp = spawnText; spawnText = (x, y, t, col, s, crit) => { if (crit) cr.push(t); }; chainLightning(a, 4, 1000); spawnText = sp; return [b.hp === 1e15 && c.hp === 1e15, a.hp < 1e15, cr.length]; })()")
    assert r[0] is True and r[1] is True and r[2] >= 1             # все разряды в цель, молнии критуют
    assert abs(js(page, "ST.ru.kirinCrit") - 0.25) < 1e-9


def test_shatter(page):
    run(page, BASE + "put('w', ['spirit', 'pierce', 'elem']); ST.critChance = 1; Math.random = () => 0.5;")
    r = js(page, "(() => { " + DUMMY + " const s = eSt(d); s.ice = {n: 2, t: 3}; dealDamage(d, 1000); const a = G.dsess.tot.katana; G.dsess = null; d.st = null; dealDamage(d, 1000); const b = G.dsess.tot.katana; return [a / b, (d.st.ice && d.st.ice.n) || 0]; })()")
    assert abs(r[0] - (js(page, "ST.critDmg") + 0.8) / js(page, "ST.critDmg")) < 1e-6
    assert js(page, "(() => { ST.critChance = 1; const d = G.dummy; d.st = null; eSt(d).ice = {n: 3, t: 3}; dealDamage(d, 10); return (d.st.ice && d.st.ice.n) || 0; })()") <= 1   # раскол снял лёд; ледяная руна слота 3 может наложить 1 заново


def test_acid(page):
    run(page, BASE + "put('w', ['elem', 'poison', 'pierce']);")
    r = js(page, "(() => { " + DUMMY + " applyElem(d, 'poison', 100, 'poison'); applyElem(d, 'fire', 100, 'fire'); return [d.st.smoke && d.st.smoke.t > 0, d.st.cr && d.st.cr.n]; })()")
    assert r[0] is True and r[1] == 8                               # полный «Раскол»: 60% / 8% = 8 стаков


def test_toxic(page):
    run(page, BASE + "put('w', ['poison', 'elem', 'time']);")
    spy = "const log = []; const dd = dealDamage; window.dealDamage = (e, dm, o) => { if (o && o.src === 'chain') log.push(e); return dd(e, dm, o); };"
    r = js(page, "(() => { Math.random = () => 0; G.enemies.length = 0; " + MOBS + spy + " const a = mk(40, 0), b = mk(40, 40); hero.swingCount = 1; heroAttack(a); window.dealDamage = dd; return [log.includes(a), log.includes(b)]; })()")
    assert r == [True, True]                                         # внеочередной вихрь — молния каждому задетому
    r = js(page, "(() => { Math.random = () => 0.99; G.enemies.length = 0; " + MOBS + spy + " const a = mk(40, 0), b = mk(40, 40); hero.swingCount = 3; heroAttack(a); window.dealDamage = dd; return log.includes(b); })()")
    assert r is False                                                # обычный вихрь (каждый 4-й) — без молний


def test_unbreakable_wave(page):
    run(page, BASE + "put('w', ['heart', 'pierce', 'time']); Math.random = () => 0.99;")
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(40, 0), b = mk(-60, 30); hero.shield = ST.ru.shCap; const sh = hero.shield; hero.swingCount = 3; heroAttack(a); return [hero.shield <= sh / 2 + ST.maxHp * 0.021, 1e15 - b.hp >= sh / 2 * 5 * ST.skillMul * 0.9]; })()")   # волна растёт с силой способностей
    assert r == [True, True]
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(40, 0); hero.shield = ST.ru.shCap * 0.5; const sh = hero.shield; hero.swingCount = 3; heroAttack(a); return hero.shield <= sh / 2 + ST.maxHp * 0.011; })()")
    assert r is True                                                 # половины щита хватает
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(40, 0); hero.shield = ST.ru.shCap * 0.4; const sh = hero.shield; hero.swingCount = 3; heroAttack(a); return hero.shield >= sh; })()")
    assert r is True                                                 # меньше половины — волны нет
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(40, 0); hero.shield = ST.ru.shCap; const sh = hero.shield; hero.swingCount = 1; heroAttack(a); return hero.shield >= sh - 1e-6; })()")
    assert r is True                                                 # без вихря — волны нет


def test_pack(page):
    run(page, BASE + "S.pets.owned.cat = {lvl: 20, xp: 0, picks: []}; S.pets.active = 'cat'; spawnPetEntity(); put('w', ['bond', 'shade', 'time']); ST.critChance = 0; Math.random = () => 0.5;")
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " G.pet.x = hero.x; G.pet.y = hero.y + 200; const e = mk(80, 200); G.pet.ultT = 10; hero.dashCd = 0; tryDash({x: 1, y: 0, mag: 1}); return [1e15 - e.hp, ST.dmg * ST.skillMul * ST.ru.shadeDmg * 0.5 * physMul({src:'shade'}), G.pet.ultT]; })()")
    assert abs(r[0] / r[1] - 1) < 0.01 and abs(r[2] - 7) < 1e-6


# ---------- Task 3: доспех ----------
PET = "S.pets.owned.cat = {lvl: 20, xp: 0, picks: []}; S.pets.active = 'cat'; spawnPetEntity();"
CALM = "Math.random = () => 0.99; hero.iframe = 0; hero.dashT = 0;"


def test_veil(page):
    run(page, BASE + "put('a', ['elem', 'elem', 'elem']);")
    r = js(page, "(() => { hero.shield = 0; G.veilT = 0; runeTick(0.016); const a = hero.shield; refreshStats(); const b = hero.shield; hero.shield = 0; runeTick(0.016); return [a / ST.maxHp, b / ST.maxHp, hero.shield]; })()")
    assert abs(r[0] - 0.2) < 1e-6 and abs(r[1] - 0.2) < 1e-6 and r[2] == 0   # щит 20% держится и не чаще раза в 10 с
    run(page, "put('a', ['elem', 'elem', null]);")
    assert js(page, "(() => { hero.shield = 0; G.veilT = 0; runeTick(0.016); return hero.shield; })()") == 0


def test_fortress(page):
    run(page, BASE + "put('a', ['heart', 'spirit', null]);")
    b0 = js(page, "ST.block")
    run(page, "put('a', ['heart', 'spirit', 'pierce']);")
    assert abs(js(page, "ST.block") - min(0.6, b0 + 0.12)) < 1e-6
    r = js(page, "(() => { Math.random = () => 0.5; ST.dodge = 0; ST.block = 1; hero.iframe = 0; hero.dashT = 0; hero.shield = 0; damageHero(1); return hero.shield / ST.maxHp; })()")
    assert abs(r - 0.06) < 1e-6                                       # блок → щит 6% здоровья


def test_ghost(page):
    run(page, BASE + "put('a', ['shade', 'time', 'spirit']);")
    r = js(page, "(() => { Math.random = () => 0; ST.dodge = 1; hero.iframe = 0; hero.dashT = 0; hero.dashCd = 5; damageHero(10); const a = hero.dashCd; hero.dashCd = 5; damageHero(10); return [a, hero.dashCd]; })()")
    assert r == [0, 5]                                                # уклон сбрасывает рывок, не чаще раза в 3 с


def test_pure(page):
    run(page, BASE + "put('a', ['poison', 'heart', null]);")
    g0 = js(page, "ST.regen")
    run(page, "put('a', ['poison', 'heart', 'elem']);")               # Стихия в 3-м слоте = лёд
    assert abs(js(page, "ST.regen") - g0 - 0.006 * js(page, "ST.healMul")) < 1e-9
    r = js(page, "(() => { S.curses.weak = 2; refreshStats(); G.pureT = 0; runeTick(0.016); const a = curseTotal(); runeTick(0.016); return [a, curseTotal(), G.pureT - G.time]; })()")
    assert r[0] == 1 and r[1] == 1 and abs(r[2] - 12) < 1e-6         # одно проклятие раз в 12 с


def test_friend(page):
    run(page, BASE + PET + "put('a', ['bond', 'heart', 'shade']);")
    r = js(page, "(() => { " + CALM + " G.friendT = G.friendCd = 0; hero.shield = 0; hero.hp = ST.maxHp * 0.31; damageHero(ST.maxHp * 0.1); return [G.friendT - G.time, G.friendCd - G.time]; })()")
    assert abs(r[0] - 3) < 1e-6 and abs(r[1] - 30) < 1e-6
    r = js(page, "(() => { " + CALM + " hero.hp = ST.maxHp; hero.shield = 0; let h = hero.hp; damageHero(100); const l1 = h - hero.hp; G.friendT = 0; hero.iframe = 0; hero.shield = 0; h = hero.hp; damageHero(100); return l1 / (h - hero.hp); })()")
    assert abs(r - 0.4) < 1e-6                                        # −60% урона
    assert js(page, "(() => { " + CALM + " G.friendT = G.friendCd = 0; G.pet = null; hero.hp = ST.maxHp * 0.31; damageHero(ST.maxHp * 0.1); return G.friendT; })()") == 0  # без питомца — никак


def test_with_you(page):
    run(page, BASE + PET + "put('a', ['bond', 'time', 'heart']); G.scrollCd = 0; S.inv.scroll = 3;")
    r = js(page, "(() => { G.withYouCd = 0; hero.hp = 0; heroDie(); const a = [hero.dead, hero.hp / ST.maxHp, hero.iframe, S.inv.scroll]; hero.hp = 0; heroDie(); return a.concat([S.inv.scroll]); })()")
    assert r[0] is False and abs(r[1] - 0.3) < 1e-6 and r[2] == 1.5 and r[3] == 3 and r[4] == 2   # второй раз — уже свиток


def test_with_you_cat(page):
    run(page, BASE + PET + "put('a', ['bond', 'time', 'heart']); PFX.ult = 'ninelives'; G.pet.ultT = 0; G.scrollCd = 0; S.inv.scroll = 3;")
    r = js(page, "(() => { G.withYouCd = 0; hero.hp = 0; heroDie(); return [hero.dead, hero.hp / ST.maxHp, G.pet.ultT, S.inv.scroll, G.withYouCd]; })()")
    assert r[0] is False and abs(r[1] - 0.2) < 1e-6 and abs(r[2] - 60) < 1e-6 and r[3] == 3 and r[4] == 0   # спас кот, откат 60 с


# ---------- Task 4: бижутерия ----------
def test_crown(page):
    run(page, BASE + "put('j', ['elem', 'elem', 'elem']);")
    r = js(page, "(() => { " + DUMMY + " G.crownT = 0; applyElem(d, 'fire', 100, 'fire'); applyElem(d, 'poison', 100, 'poison'); return [G.crownT - G.time, runeAtkCd() / ST.atkCd]; })()")
    assert abs(r[0] - 3) < 1e-6 and abs(r[1] - 1 / 1.1) < 1e-9
    run(page, "put('j', ['elem', 'elem', null]);")
    r = js(page, "(() => { " + DUMMY + " G.crownT = 0; applyElem(d, 'fire', 100, 'fire'); applyElem(d, 'poison', 100, 'poison'); return [G.crownT, runeAtkCd() === ST.atkCd]; })()")
    assert r == [0, True]


def test_dance(page):
    run(page, BASE + "put('j', ['spirit', 'pierce', 'shade']);")
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " Math.random = () => 0.5; const a = mk(40, 0), b = mk(140, 0), c = mk(500, 0); eSt(a).mk = {n: 9, t: G.time + 4}; runeMark(a); return [(1e15 - b.hp) / (1e15 - a.hp), c.hp === 1e15]; })()")
    assert abs(r[0] - 0.5) < 0.01 and r[1] is True


def test_haven(page):
    run(page, BASE + "put('j', ['poison', 'heart', 'time']);")
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(100, 0), b = mk(500, 0); G.breathCd = 0; hero.hp = ST.maxHp * 0.2; runeBreath(ST.maxHp * 0.31); return [G.breathCd - G.time, !!(a.st && a.st.poison && a.st.poison.n), !!(b.st && b.st.poison && b.st.poison.n)]; })()")
    assert abs(r[0] - 30) < 1e-6 and r[1] is True and r[2] is False


def test_union(page):
    run(page, BASE + "put('j', ['bond', 'elem', 'time']);")
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(100, 0); petHitArea(a.x, a.y, 50, 1, '#fff'); return !!(a.st && a.st.zap && a.st.zap.t > 0); })()")
    assert r is True
    run(page, "put('j', ['bond', null, 'time']);")
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(100, 0); petHitArea(a.x, a.y, 50, 1, '#fff'); return !!(a.st && a.st.zap && a.st.zap.t > 0); })()")
    assert r is False


def test_fury(page):
    run(page, BASE + "S.oni = true; put('j', ['elem', 'time', 'spirit']); S.oniCd = 0; S.oniE = 100;")
    r = js(page, "(() => { tryOniSuper(); return [G.oniSuperT - (PFX.superDur || 0), S.oniCd, Math.max(150, (240 - (PFX.superCd || 0)) * (1 - (ST.ru.oniCd || 0)))]; })()")
    assert abs(r[0] - 14) < 1e-6 and abs(r[1] - r[2]) < 1e-6
    r = js(page, "(() => { " + DUMMY + " ST.critChance = 1; dealDamage(d, 10); const a = !!(d.st.fire && d.st.fire.n); G.oniSuperT = 0; d.st = null; dealDamage(d, 10); return [a, !!(d.st.fire && d.st.fire.n)]; })()")
    assert r == [True, False]                                         # в Ярости физ. крит поджигает


def test_sakura_calm_limits(page):
    run(page, BASE + "put('j', ['spirit', 'shade', 'time']);")
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(80, 30), b = mk(80, 300), c = mk(120, -20); c.mini = true; hero.dashCd = 0; tryDash({x: 1, y: 0, mag: 1}); const out = [(a.calmT || 0) - G.time, b.calmT || 0, c.st && c.st.stun && c.st.stun.t, c.calmT || 0]; a.calmT = 0; c.st.stun.t = 0; hero.dashCd = 0; tryDash({x: 1, y: 0, mag: 1}); return out.concat([a.calmT, c.st.stun.t]); })()")
    assert abs(r[0] - 1.5) < 1e-6 and r[1] == 0 and abs(r[2] - 0.3) < 1e-6 and r[3] == 0
    assert r[4] == 0 and r[5] == 0                                    # повтор на того же врага — не раньше чем через 6 с
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(80, 30); a.calmT = G.time + 1; a.cd = 0; updateEnemy(a, 0.016); return a.cd > 0; })()")
    assert r is True                                                  # спокойный враг не атакует


# ---------- финальное ревью ----------
def test_fortress_block_never_lowers_shield(page):
    run(page, BASE + "put('a', ['heart', 'spirit', 'pierce']);")
    r = js(page, "(() => { Math.random = () => 0.5; ST.dodge = 0; ST.block = 1; hero.iframe = 0; hero.dashT = 0; hero.shield = ST.maxHp * 0.6; const s0 = hero.shield; damageHero(1); return hero.shield >= s0 - 1; })()")
    assert r is True


def test_haven_poison_deals_damage_without_poison_weapon(page):
    run(page, BASE + "put('j', ['poison', 'heart', 'time']);")
    r = js(page, "(() => { G.enemies.length = 0; " + MOBS + " const a = mk(100, 0); G.breathCd = 0; hero.hp = ST.maxHp * 0.2; runeBreath(ST.maxHp * 0.31); return [ST.elV.poison, a.st.poison.dps]; })()")
    assert r[0] == 0 and r[1] > 0


def test_pack_skips_nine_lives(page):
    run(page, BASE + "S.pets.owned.cat = {lvl: 20, xp: 0, picks: []}; S.pets.active = 'cat'; spawnPetEntity(); put('w', ['bond', 'shade', 'time']);")
    r = js(page, "(() => { PFX.ult = 'ninelives'; G.pet.ultT = 10; hero.dashCd = 0; tryDash({x: 1, y: 0, mag: 1}); return G.pet.ultT; })()")
    assert r == 10                                                    # «Стая» не ускоряет спасение кота

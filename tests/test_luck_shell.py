from conftest import js, run, frames, load_save


def test_luck_best_of_two(page):
    run(page, "ST.luckRoll = 1; window.__seq = [0.1, 0.9]; window.__i = 0; window.__r = Math.random; Math.random = () => __seq[(__i++) % 2]; window.__q = rollQ(); Math.random = __r;")
    assert abs(js(page, "__q") - (0.85 + 0.9 * 0.3)) < 1e-9
    run(page, "ST.luckRoll = 0; window.__i = 0; Math.random = () => __seq[(__i++) % 2]; window.__q = rollQ(); Math.random = __r;")
    assert abs(js(page, "__q") - (0.85 + 0.1 * 0.3)) < 1e-9


def test_luck_distribution_shifts(page):
    m = js(page, "(() => { ST.luckRoll = 0.6; let s = 0; for (let i = 0; i < 2000; i++) s += rollQ(); return s / 2000; })()")
    assert m > 1.02


def test_luck_from_jewelry(page):
    run(page, "S.ring.ench = [{id: 'luck', t: 5, v: 60}]; refreshStats();")
    assert abs(js(page, "ST.luckRoll") - 0.6) < 1e-9


SH = "S.a.ench = [{id: 'shell', t: 5, v: 120}, null, null, null]; refreshStats(); G.god = false; hero.iframe = 0; hero.dashT = 0; hero.shield = 0; ST.reduce = 0; ST.block = 0; ST.res = {}; hero.hp = ST.maxHp;"


def test_shell_stacks_from_hit_dodge_block(page):
    run(page, SH + " ST.dodge = 0; damageHero(1); hero.iframe = 0;")
    assert js(page, "G.shellN") == 1
    run(page, "ST.dodge = 1; damageHero(1); hero.iframe = 0; ST.dodge = 0; ST.block = 1; damageHero(1); hero.iframe = 0;")
    assert js(page, "G.shellN") == 3


def test_shell_decay(page):
    run(page, SH + " ST.dodge = 0; damageHero(1); hero.iframe = 0; damageHero(1);")
    assert js(page, "G.shellN") == 2
    run(page, "for (let i = 0; i < 125; i++) shellTick(1/60);")
    assert js(page, "G.shellN") == 1


def test_shell_reduction_and_speed(page):
    run(page, SH + " const sp0 = ST.speed, cd0 = ST.atkCd; window.__b = [sp0, cd0]; ST.dodge = 0; G.shellN = 5; G.shellT = 2; refreshStats(); ST.dodge = 0; ST.reduce = 0; ST.block = 0; hero.iframe = 0; hero.shield = 0; ST.res = {};")
    sp0, cd0 = js(page, "__b")
    assert abs(js(page, "ST.speed") / sp0 - 0.85) < 1e-9 and abs(cd0 / js(page, "ST.atkCd") - 0.85) < 1e-9
    got = js(page, "(() => { hero.hp = ST.maxHp; const h = hero.hp; damageHero(100); return h - hero.hp; })()")
    assert abs(got - 80) < 1e-6


def test_shell_reflect_kill(page):
    run(page, SH + " ST.dodge = 0; G.shellN = 5; G.shellT = 2; const e = makeDummy(); e.dummy = false; e.type = 'bruiser'; e.hp = 10; e.maxHp = 1000; e.x = hero.x + 100; e.y = hero.y; G.enemies.push(e); window.__e = e; window.__k = S.kills; damageHero(100, e);")
    assert js(page, "__e.dead") is True and js(page, "S.kills - __k") == 1


def test_migrate_thorns(page, V6):
    d = dict(V6); a = dict(d['a']); a['ench'] = [{'id': 'thorns', 't': 3, 'v': 55}, None, None, None]; d['a'] = a; d.pop('elemMig', None)
    load_save(page, d)
    assert js(page, "S.a.ench[0]") == {"id": "shell", "t": 3, "v": 55}


def test_migrate_tower_profile(page, V6):
    d = dict(V6); d.pop('elemMig', None)
    load_save(page, d)
    run(page, "towerEnter(1, 1); S.a.ench = [{id: 'thorns', t: 2, v: 35}, null]; S.mainStash.w.ench = [{id: 'burn', t: 5, v: 90}, null, null, null]; S.elemMig = 0; save(); G.noSaveOnUnload = true;")
    page.reload(); page.wait_for_function("typeof S==='object' && S.stars", polling=100)
    assert js(page, "S.w.ench[0].v") == 36
    run(page, "towerEnter(1, 1);")
    assert js(page, "S.a.ench[0].id") == "shell"


def test_hud_shell_icon(page):
    run(page, "window.__txt = []; const f = CanvasRenderingContext2D.prototype.fillText; CanvasRenderingContext2D.prototype.fillText = function (t, ...a) { __txt.push(String(t)); return f.call(this, t, ...a); };" + SH + " G.shellN = 3; G.shellT = 99;")
    frames(page, 3)
    assert "🛡3" in js(page, "__txt")

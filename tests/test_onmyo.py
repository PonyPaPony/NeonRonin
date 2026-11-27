"""Этап 3: особый босс 50-го этажа — Куроями, тёмный онмёдзи."""
from conftest import js, run

ENTER = ("runCmd('открыть всё'); runCmd('soul 100'); travelTo(3); fixSlots(); runCmd('tower'); S.tower.cp = 41; S.tower.kills = 0; refreshStats();"
         "towerEnter(41, 1); runCmd('twfloor 50'); G.god = true; towerSpawns(0.016);"
         "window.B = () => G.tw.boss; window.lan = () => G.enemies.filter(e => e.lantern && !e.dead);"
         "window.hitL = l => { for (let i = 0; i < 10 && !l.dead; i++) { G.time += 0.2; dealDamage(l, 1, {noKb: true}); } };")


# ---------- Task 3 ----------
def test_onmyo_spawns_on_50(page):
    run(page, ENTER)
    r = js(page, "[!!B() && !!B().onmyo, B() && B().name, B() && B().onmyo.ph]")
    assert r[0] is True and 'онмёдзи' in r[1] and r[2] == 1
    run(page, "runCmd('twfloor 40'); towerSpawns(0.016);")
    assert js(page, "!!(G.tw.boss && G.tw.boss.onmyo)") is False


def test_phase_threshold_clamp(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.hp = b.maxHp * 0.67; dealDamage(b, b.maxHp * 0.5, {noKb: true, noProc: true}); return [b.hp / b.maxHp, b.onmyo.shield, lan().length]; })()")
    assert abs(r[0] - 0.66) < 1e-9 and r[1] is True and r[2] == 3     # крит не перепрыгивает порог: щит и 3 фонаря


def test_shield_and_lanterns_phase1(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.hp = b.maxHp * 0.66 + 1; dealDamage(b, 10, {noKb: true, noProc: true}); const h = b.hp; dealDamage(b, b.maxHp * 0.1, {noKb: true, noProc: true}); elemDmg(b, 'fire', b.maxHp * 0.1, 'fire');"
                 " const blocked = b.hp === h; const L = lan(); hitL(L[0]); hitL(L[1]); const sh2 = b.onmyo.shield; hitL(L[2]); return [blocked, sh2, b.onmyo.shield, b.onmyo.ph]; })()")
    assert r == [True, True, False, 2]                                  # щит держит, последний фонарь снимает щит → фаза 2


def test_dmg_buff_by_tower_level(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); const d0 = b.dmg; b.hp = b.maxHp * 0.66; dealDamage(b, 10, {noKb: true, noProc: true}); const L = lan(); hitL(L[0]); hitL(L[1]); hitL(L[2]); return b.dmg / d0; })()")
    assert abs(r - 1.02 ** 2) < 1e-6                                   # уровень Башни 1: +2% за каждый из первых двух фонарей
    run(page, "towerExit && towerExit(); S.tower.kills = 98 * 10000; S.tower.charges = 2; S.tower.run = null; towerEnter(41, 99); runCmd('twfloor 50'); towerSpawns(0.016);")
    r = js(page, "(() => { const b = B(); const d0 = b.dmg; b.hp = b.maxHp * 0.66; dealDamage(b, 10, {noKb: true, noProc: true}); let L = lan(); for (const l of L) hitL(l);"
               " b.hp = b.maxHp * 0.33; dealDamage(b, 10, {noKb: true, noProc: true}); L = lan(); const n = L.length; for (const l of L) hitL(l); return [b.dmg / d0, n, b.onmyo.ph]; })()")
    assert abs(r[0] - 1.10 ** 2 * 1.12 ** 5) < 1e-6 and r[1] == 6 and r[2] == 3


def test_lanterns_not_enemies(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.hp = b.maxHp * 0.66; dealDamage(b, 10, {noKb: true, noProc: true}); const k0 = S.tower.kills; for (const l of lan()) hitL(l); return [S.tower.kills - k0, towerFloorCleared(), G.loot.filter(l => l.type === 'gold').length]; })()")
    assert r == [0, False, 0]                                           # фонари не убийства, не добыча, этаж не пройден


def test_onmyo_death_keeps_state(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.hp = b.maxHp * 0.66; dealDamage(b, 10, {noKb: true, noProc: true}); hitL(lan()[0]); const e0 = S.tower.run.endTs; hero.x = TW.CX; hero.y = TW.CY + 200; towerRespawn();"
                 " return [G.tw.boss === b, b.hp / b.maxHp, b.onmyo.shield, lan().length, Math.round((e0 - S.tower.run.endTs) / 1000), hero.x === TW.CX, hero.iframe]; })()")
    assert r == [True, 0.66, True, 2, 300, True, 2]                    # на месте, босс как был, −5 минут


def test_onmyo_death_short_timer_ends_run(page):
    run(page, ENTER + "S.tower.run.endTs = Date.now() + 200 * 1000; towerRespawn(); towerUpdate(0.016);")
    assert js(page, "!!G.twEndAt") is True                              # осталось меньше 5 минут — заход заканчивается


def test_egg_first_win_only(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.onmyo.ph = 4; b.hp = 1; dealDamage(b, 100, {noKb: true, noProc: true}); return [S.tower.onmyoWin, S.pets.eggs.filter(e => e.sp === 'chochin').length]; })()")
    assert r == [True, 1]
    run(page, "runCmd('twfloor 50'); towerSpawns(0.016);")
    r = js(page, "(() => { const b = B(); b.onmyo.ph = 4; b.hp = 1; G.loot.length = 0; dealDamage(b, 100, {noKb: true, noProc: true}); return [S.pets.eggs.filter(e => e.sp === 'chochin').length, G.loot.filter(l => l.type === 'rfrag').length]; })()")
    assert r == [1, 8]                                                 # повторно — без яйца, 8 фрагментов


def test_execute_cannot_skip_phases(page):
    run(page, ENTER + "ST.execute = 0.5; refreshStats = refreshStats;")
    r = js(page, "(() => { const b = B(); ST.execute = 0.9; b.hp = b.maxHp * 0.67; dealDamage(b, 1, {noKb: true, noProc: true}); return [!!b.dead, b.hp > 0]; })()")
    assert r == [False, True]


def test_auto_hits_lanterns(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.hp = b.maxHp * 0.66; dealDamage(b, 10, {noKb: true, noProc: true}); G.autoHunt = true; G.autoAnchor = {x: b.x, y: b.y}; hero.x = b.x - 60; hero.y = b.y; G.autoT = 0; G.autoTarget = null; autoHuntInput(hero, 0.016); return !!(G.autoTarget && G.autoTarget.lantern); })()")
    assert r is True


# ---------- Task 4 ----------
def test_talisman_trap(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.onmyo.ph = 2; b.onmyo.talT = 0; G.telegraphs.length = 0; onmyoTick(b, 0.016); const T = G.telegraphs.filter(t => t.ofuda); hero.slowT = 0; hero.x = T[0].x; hero.y = T[0].y; T[0].onFire(); return [T.length >= 1, hero.slowT > 0]; })()")
    assert r == [True, True]


def test_lions_summon(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.onmyo.ph = 2; for (let i = 0; i < 5; i++) { b.onmyo.lionT = 0; onmyoTick(b, 0.016); } return G.enemies.filter(e => e.lion && !e.dead).length; })()")
    assert r == 3                                                      # во второй фазе — не больше 3 львов сразу


def test_captive_spirits_freed_by_hit(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.onmyo.ph = 2; b.hp = b.maxHp * 0.34; dealDamage(b, b.maxHp * 0.1, {noKb: true, noProc: true}); const C = G.enemies.filter(e => e.captive && !e.dead), k0 = S.tower.kills;"
                 " const c = C[0]; c.oa = -0.16; hero.x = c.anchor.x + 65; hero.y = c.anchor.y; const hx = hero.x; updateEnemy(c, 0.1); const pushed = Math.abs(hero.x - hx) > 1; dealDamage(c, 1, {noKb: true}); return [C.length, pushed, c.dead, S.tower.kills - k0]; })()")
    assert r[0] >= 4 and r[1] is True and r[2] is True and r[3] == 0  # духи отталкивают, удар освобождает (не убийство)


def test_phase3_curses(page):
    run(page, ENTER + "G.god = false; S.curses = {}; ST.curseRes = 0;")
    r = js(page, "(() => { const b = B(); b.onmyo.ph = 3; b.onmyo.curseT = 0; Math.random = () => 0.01; onmyoTick(b, 0.016); G.god = true; return Object.values(S.curses).reduce((a, x) => a + x, 0); })()")
    assert r == 1


def test_final_lantern_only_chochin(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.onmyo.ph = 3; b.hp = b.maxHp * 0.02; dealDamage(b, b.maxHp * 0.5, {noKb: true, noProc: true}); const L = lan(), n = L.length, ch = L.filter(l => l.chochinL);"
                 " const wrong = L.find(l => !l.chochinL); const lions0 = G.enemies.filter(e => e.lion && !e.dead).length; hitL(wrong); const lions1 = G.enemies.filter(e => e.lion && !e.dead).length; const sh1 = b.onmyo.shield;"
                 " hitL(ch[0]); return [n, ch.length, lions1 - lions0, sh1, b.onmyo.shield, b.onmyo.ph, b.hp / b.maxHp]; })()")
    assert r[:6] == [9, 1, 1, True, False, 4] and abs(r[6] - 0.01) < 1e-9


def test_talisman_hint_on_floor_50(page):
    run(page, ENTER + "window.__bn = []; const _b = banner; window.banner = (a, b) => { __bn.push(a + ' ' + b); return _b(a, b); }; runCmd('twfloor 50'); towerSpawns(0.016);")
    assert any('талисман' in x for x in js(page, "__bn"))


# ---------- Task 5: вспышки и FPS ----------
def test_flash_onmyo_all_phases(page):
    run(page, ENTER + "S.pets.owned.chochin = {lvl: 50, xp: 0, picks: [1,1,1,1,1,0], x2: []}; S.pets.active = 'chochin'; spawnPetEntity(); refreshPetFx(); toggleAuto(true);"
              "window.__fl = 0; setInterval(() => { if (G.flash > 0) window.__fl++; for (const e of G.enemies) if (e.boss && e.flash > 0) window.__fl++; }, 16);")
    for th in (0.67, 0.34, 0.02):
        run(page, f"(() => {{ const b = B(); for (const e of G.enemies) if (e.lantern || e.captive) e.dead = true; b.onmyo.shield = false; b.onmyo.ph = {1 if th > 0.6 else 2 if th > 0.3 else 3}; b.hp = b.maxHp * {th}; }})()")
        page.wait_for_timeout(2500)
    assert js(page, "[window.__fl, B() ? B().hp > 0 : true]") == [0, True]


def _fps(browser, url, floor):
    from conftest import _open
    ctx, p = _open(browser, url); cdp = ctx.new_cdp_session(p); cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
    p.evaluate(f"() => {{ runCmd('unlock3'); travelTo(3); runCmd('tower'); S.tower.cp = 41; towerEnter(41, 1); runCmd('twfloor {floor}'); G.god = true; GFX.mode = 'mid'; GFX.level = 1; towerSpawns(0.016); }}")
    if floor == 50:
        p.evaluate("() => { const b = G.tw.boss; b.onmyo.ph = 3; b.hp = b.maxHp * 0.02; dealDamage(b, b.maxHp, {noKb: true, noProc: true}); onmyoLions(b, 4); }")
    p.evaluate("() => toggleAuto(true)")
    p.wait_for_timeout(2500)
    f = p.evaluate("() => new Promise(r => { let n = 0; const t0 = performance.now(); const k = () => { n++; if (performance.now() - t0 < 3000) requestAnimationFrame(k); else r(n / ((performance.now() - t0) / 1000)); }; requestAnimationFrame(k); })")
    ctx.close(); return f


def test_fps_onmyo_phase3(browser, srv):
    med = lambda l: sorted(l)[1]
    f40 = med([_fps(browser, srv, 40) for _ in range(3)])
    f50 = med([_fps(browser, srv, 50) for _ in range(3)])
    print('fps 40 / 50:', f40, f50)
    assert f50 >= 0.85 * f40


# ---------- финальное ревью этапа 3 ----------
SH = "const b = B(); b.hp = b.maxHp * 0.66; dealDamage(b, 10, {noKb: true, noProc: true});"


def test_review_real_death_path(page):
    run(page, ENTER)
    r = js(page, "(() => { " + SH + " hero.x = TW.CX; hero.y = TW.CY + 150; G.god = false; G.autoHunt = true; hero.iframe = 0; hero.hp = 1; heroDie(); heroRespawn(); G.god = true;"
                 " const hp1 = b.hp / b.maxHp; updateBoss(b, 1, 0, 0, 0, false); return [hero.x, hero.y, hp1, b.hp / b.maxHp, G.autoAnchor.x]; })()")
    assert r[0] == js(page, "TW.CX") and r[2] == 0.66 and r[3] == 0.66 and r[4] == r[0]


def test_review_captives_freed_with_lantern(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.onmyo.ph = 2; b.hp = b.maxHp * 0.34; dealDamage(b, b.maxHp * 0.1, {noKb: true, noProc: true}); const c = G.enemies.find(e => e.captive && !e.dead); hitL(c.anchor); return c.dead; })()")
    assert r is True


def test_review_thorns_respect_shield(page):
    run(page, ENTER)
    r = js(page, "(() => { " + SH + " G.god = false; hero.iframe = 0; ST.dodge = 0; ST.block = 0; ST.shellRefl = 1e9; ST.shellR = 0.1; G.shellN = 5; Math.random = () => 0.99; damageHero(1000, b); G.god = true; return b.hp / b.maxHp; })()")
    assert r == 0.66


def test_review_lions_die_with_boss(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); onmyoLions(b, 2); b.onmyo.ph = 4; b.hp = 1; dealDamage(b, 100, {noKb: true, noProc: true}); return G.enemies.filter(e => e.lion && !e.dead).length; })()")
    assert r == 0


def test_review_final_aoe_does_not_break_wrong(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.onmyo.ph = 3; b.hp = b.maxHp * 0.02; dealDamage(b, b.maxHp, {noKb: true, noProc: true}); const w = lan().find(l => !l.chochinL); for (let i = 0; i < 6; i++) { G.time += 0.2; dealDamage(w, 1, {src: 'chain', el: 'thunder', noKb: true}); dealDamage(w, 1, {src: 'wave', noKb: true}); } applyElem(w, 'fire', 100, 'fire'); return [w.hits, !!(w.st && w.st.fire)]; })()")
    assert r == [4, False]                                             # в финале фонари бьются только катаной/вихрем/Тенью


def test_review_lanterns_spread_and_auto_reach(page):
    run(page, ENTER)
    r = js(page, "(() => { const b = B(); b.x = TW.AX0 + 80; b.y = TW.AY0 + 90; b.onmyo.ph = 3; b.hp = b.maxHp * 0.02; dealDamage(b, b.maxHp, {noKb: true, noProc: true}); const L = lan(); let minD = 1e9; for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) minD = Math.min(minD, dist(L[i].x, L[i].y, L[j].x, L[j].y));"
                 " G.autoHunt = true; G.autoAnchor = {x: TW.AX1 - 100, y: TW.CY}; hero.x = TW.AX1 - 120; hero.y = TW.CY; G.autoT = 0; G.autoTarget = null; autoHuntInput(hero, 0.016); return [minD, !!(G.autoTarget && G.autoTarget.lantern)]; })()")
    assert r[0] > 60 and r[1] is True


def test_review_spirit_shield_survives_refresh(page):
    run(page, ENTER + "towerExit && towerExit(); travelTo(3); S.pets.owned.chochin = {lvl: 50, xp: 0, picks: [1,1,1,1,1,1], x2: []}; S.pets.active = 'chochin'; spawnPetEntity(); refreshPetFx(); refreshStats();")
    r = js(page, "(() => { hero.shield = 0; G.pet.spT = 0; updatePet(0.016); const a = hero.shield; refreshStats(); return [a / ST.maxHp, hero.shield / ST.maxHp]; })()")
    assert abs(r[0] - 0.05) < 1e-6 and abs(r[1] - 0.05) < 1e-6

"""Стенд 2в: билды PonyPaPony (замеры 27.11) против Сютэн-додзи — босс один, босс с толпой, «физ. урон ×0,1».
Запуск: pytest tests/test_stand_2v.py -m slow -s"""
import json
import pytest
from conftest import js, run

BASE_BUILD = {
    "soul": {k: 20 for k in ["pow", "vit", "def", "acc", "fury", "life", "agi", "greed"]},
    "stars": {"pow": 10, "vit": 0, "def": 0, "acc": 0, "fury": 0, "life": 0, "agi": 0, "greed": 11},
    "tree": {"seed": 5, "guard": 10, "bark": 5, "eye": 10, "poison": 8, "curse": 8, "fire": 8, "ice": 8, "thunder": 8, "pierce": 10},
    "village": {k: 3 for k in ["ratusha", "herald", "forge", "shop", "nursery", "tea", "spring", "shrine", "house1", "house2", "house3", "house4", "palisade", "tower1", "tower2"]},
    "a": [{"id": "speed", "t": 5, "v": 40.9}, {"id": "shell", "t": 5, "v": 175.3}, {"id": "eshield", "t": 5, "v": 65.7}, {"id": "dodge", "t": 5, "v": 26.3}],
}
EN = {"vamp": {"id": "vamp", "t": 5, "v": 14.6}, "crit": {"id": "crit", "t": 5, "v": 32.1, "v2": 146}, "chain": {"id": "chain", "t": 5, "v": 43.8},
      "execute": {"id": "execute", "t": 5, "v": 29.2}, "frost": {"id": "frost", "t": 5, "v": 40.9}, "burn": {"id": "burn", "t": 5, "v": 52.6}, "poison": {"id": "poison", "t": 5, "v": 46.7}}
BUILDS = {  # оружие, руны катана/доспех/бижутерия, 2-я чара украшений
    "физ. Кирин":      (["vamp", "crit", "chain", "execute"], ["pierce", "elem", "spirit"], ["pierce", "spirit", "heart"], ["spirit", "pierce", "shade"], "sharp"),
    "физ. Ронин":      (["crit", "chain", "vamp", "execute"], ["spirit", "shade", "pierce"], ["elem", "elem", "elem"], ["spirit", "pierce", "shade"], "sharp"),
    "огонь+лёд+крит":  (["frost", "burn", "vamp", "crit"], ["spirit", "pierce", "elem"], ["elem", "elem", "elem"], ["spirit", "pierce", "shade"], "surge"),
    "Аватар":          (["poison", "chain", "frost", "burn"], ["elem", "elem", "elem"], ["elem", "elem", "elem"], ["elem", "elem", "elem"], "surge"),
    "огонь+лёд+крит (Острота)": (["frost", "burn", "vamp", "crit"], ["spirit", "pierce", "elem"], ["elem", "elem", "elem"], ["spirit", "pierce", "shade"], "sharp"),
    "яд (Гроза)":      (["frost", "burn", "poison", "chain"], ["poison", "elem", "time"], ["poison", "heart", "elem"], ["poison", "heart", "time"], "surge"),
}


def setup(page, name):
    w, rw, ra, rj, j2 = BUILDS[name]
    jw = [{"id": "might", "t": 5, "v": 32.1}, {"id": j2, "t": 5, "v": 32.1, "v2": 36.5}, {"id": "skill", "t": 5, "v": 65.7}, {"id": "haste", "t": 5, "v": 29.2}]
    B = dict(BASE_BUILD, w=[EN[x] for x in w], jw=jw, rw=rw, ra=ra, rj=rj)
    run(page, "(() => { const B = " + json.dumps(B) + ";"
              " if (!S.oni) runCmd('oni'); runCmd('unlock3'); S.tower.unlocked = true; runCmd('rank_weapon 12'); runCmd('rank_armor 12'); S.w.lvl = 8; S.a.lvl = 8;"
              " Object.assign(S.soul, B.soul); if (S.stars) S.stars.b = Object.assign(S.stars.b || {}, B.stars); S.tree = Object.assign(S.tree || {}, B.tree); if (S.village) S.village.steps = Object.assign(S.village.steps || {}, B.village);"
              " for (const k of JKEYS) { S[k].lvl = 15; S[k].slot4 = true; } fixSlots(); for (const k of JKEYS) S[k].ench = B.jw.map(x => Object.assign({}, x));"
              " S.w.ench = B.w.map(x => Object.assign({}, x)); S.a.ench = B.a.map(x => Object.assign({}, x));"
              " const m = ids => ids.map(id => ({id, r: 5, f: [0,0,0,0,0,0]})); S.runes.w = m(B.rw); S.runes.a = m(B.ra); S.runes.j = m(B.rj);"
              " S.pets.active = null; G.pet = null; if (S.loc !== 3) travelTo(3); refreshPetFx && refreshPetFx(); refreshStats(); hero.hp = ST.maxHp; })()")


def fight(page, mode, timeout=40):
    """mode: 'boss' — только босс, 'crowd' — босс и обычная толпа района, 'phys' — только босс при физ. ×0,1"""
    run(page, f"(() => {{ runCmd('physmod {0.1 if mode == 'phys' else 1}'); G.god = true; G.autoBossTest = true; G.autoNoDodge = true; if (window.__clr) clearInterval(window.__clr);"
              " for (const e of G.enemies) if (!e.dummy) e.dead = true; G.enemies = G.enemies.filter(e => e.dummy); G.bosses[4] = null; G.bossTimers[4] = 0; runCmd('tp 4');"
              " const A = WORLD.arenas[3]; hero.x = A.x - 250; hero.y = A.y; G.cam.x = hero.x; G.cam.y = hero.y; const b = makeBoss(4); G.bosses[4] = b; G.enemies.push(b); G.autoAnchor = { x: hero.x, y: hero.y };"
              + (" window.__clr = setInterval(() => { for (const e of G.enemies) if (!e.boss && !e.dummy) e.dead = true; G.enemies = G.enemies.filter(e => e.boss || e.dummy); }, 30);" if mode != 'crowd' else "")
              + " window.__zr = null; if (!window.__zfw) { window.__zfw = 1; const zf = zamerFinish; window.zamerFinish = a => { if (G.zm) window.__zr = zamerResult(G.zm); return zf(a); }; }"
              " S.oniE = 0; G.speed = 2; if (!G.autoHunt) toggleAuto(true); zamerStart(); })()")
    for _ in range(timeout * 2):
        page.wait_for_timeout(500)
        if js(page, "!!(G.bosses[4] && G.bosses[4].dead)"):
            break
    page.wait_for_timeout(1700)
    r = js(page, "(() => { const R = G.zm ? zamerResult(G.zm) : window.__zr; if (window.__clr) clearInterval(window.__clr); G.speed = 1; runCmd('physmod 1');"
                 " return R ? { kill: R.boss && R.boss.kill, bossDps: R.boss && R.boss.dps, combat: R.avgCombat, src: R.src } : null; })()")
    run(page, "if (G.zm) zamerFinish('стенд'); toggleAuto(false);")
    return r


@pytest.mark.slow
@pytest.mark.parametrize("mode", ["boss", "crowd", "phys"])
def test_stand(page, mode):
    res = {}
    setup(page, "физ. Кирин"); page.wait_for_timeout(500)   # первый запуск: пробуждение Они перестраивает снаряжение
    for name in BUILDS:
        setup(page, name)
        r = fight(page, mode)
        res[name] = r
        top = sorted(((k, v) for k, v in (r or {}).get('src', {}).items()), key=lambda x: -x[1])[:5] if r else []
        print(f"[{mode}] {name}: победа {r and r['kill'] and round(r['kill'], 1)} с · по боссу {r and r['bossDps'] and round(r['bossDps'] / 1e6)} млн/с · в бою {r and round(r['combat'] / 1e6)} млн/с · {[(k, round(v / 1e6)) for k, v in top]}")
    with open(f"/tmp/stand_{mode}.json", "w") as f:
        json.dump(res, f, ensure_ascii=False)

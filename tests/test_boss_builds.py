"""Замер билдов PonyPaPony (Они, ранг 11 +8, чары тира V, бижутерия 15) на чучеле с защитой/уклонением/стихией 3-го босса гор (Ямамба)."""
import pytest, json, os
from conftest import js, run

JW = ("S.ring.lvl = S.brace.lvl = S.neck.lvl = 15;"
      "S.ring.ench = [{id:'might',t:4,v:27.4},{id:'luck',t:4,v:87.4},{id:'skill',t:4,v:64.8}];"
      "S.brace.ench = [{id:'might',t:4,v:31.9},{id:'luck',t:4,v:79.6},{id:'skill',t:4,v:61.8}];"
      "S.neck.ench = [{id:'might',t:4,v:30.8},{id:'luck',t:4,v:78},{id:'skill',t:4,v:64.2}];"
      "S.a.ench = [{id:'speed',t:4,v:40.6},{id:'shell',t:4,v:174.3},{id:'eshield',t:4,v:63.9},{id:'dodge',t:4,v:25.3}];")
SLOT4 = {'sharp': "{id:'sharp',t:5,v:30.8,v2:35}", 'might': "{id:'might',t:5,v:30.8}"}
BUILDS = {
    'физ: вамп+гром+крит+казнь': ('sharp', "[{id:'vamp',t:4,v:11.2},{id:'chain',t:4,v:42.2},{id:'crit',t:4,v:30.7,v2:139.6},{id:'execute',t:4,v:27.5}]"),
    'аватар: огонь+яд+лёд+гром': ('might', "[{id:'burn',t:4,v:50},{id:'poison',t:4,v:45},{id:'frost',t:4,v:39},{id:'chain',t:4,v:42.2}]"),
    'огонь+лёд+крит+вамп':       ('might', "[{id:'burn',t:4,v:50},{id:'frost',t:4,v:39},{id:'crit',t:4,v:30.7,v2:139.6},{id:'vamp',t:4,v:11.2}]"),
}
SETUP = ("runCmd('oni'); runCmd('unlock3'); runCmd('rank_weapon 11'); runCmd('rank_armor 11'); S.w.lvl = 8; S.a.lvl = 8;"
         "for (const s of SOUL) S.soul[s.id] = SOUL_MAX; " + JW + " travelTo(3); fixSlots(); refreshStats(); G.god = true;"
         "const b = makeBoss(3); window.__boss = { def: b.def || 0, eva: b.eva || 0, elem: b.elem || b.element || null, name: b.name };")


def measure(page, b, secs=8, speed=3):
    s4, ench = b
    run(page, f"for (const k of JKEYS) {{ S[k].slot4 = true; }} fixSlots(); for (const k of JKEYS) S[k].ench[3] = {SLOT4[s4]}; S.w.ench = {ench}; refreshStats(); G.dsess = null; const d = G.dummy; d.hp = d.maxHp = 1e18; d.def = __boss.def; d.eva = __boss.eva; d.elem = __boss.elem; d.st = null;"
              f"hero.x = DUMMY.x - 60; hero.y = DUMMY.y; S.oniE = 0; G.speed = {speed};")
    page.wait_for_timeout(secs * 1000)
    r = js(page, "(() => { const s = G.dsess, t = Math.max(0.1, (s.done ? s.end : G.time) - s.t0), o = {}; for (const k in s.tot) o[k] = s.tot[k] / t; G.speed = 1; return { total: s.sum / t, src: o }; })()")
    run(page, "hero.x = DUMMY.x - 600; G.dsess = null;"); page.wait_for_timeout(2300)
    return r


@pytest.mark.slow
def test_boss_builds(page):
    run(page, SETUP); page.wait_for_timeout(1500)
    print('цель:', js(page, "__boss"))
    res = {}
    for name, ench in BUILDS.items():
        rs = [measure(page, ench) for _ in range(2)]
        r = max(rs, key=lambda x: x['total']); r['runs'] = [round(x['total'] / 1e6, 2) for x in rs]
        res[name] = r
        print(name, json.dumps({'runs': r['runs'], 'src': {k: f"{v/1e6:.2f}M" for k, v in sorted(r['src'].items(), key=lambda x: -x[1]) if v > 1e4}}, ensure_ascii=False))
    a, f = res['аватар: огонь+яд+лёд+гром']['total'], res['физ: вамп+гром+крит+казнь']['total']
    print('аватар / физ =', round(a / f, 2))
    assert a / f <= 1.45   # стихии сильнее на слот вампиризма (решение PonyPaPony: стихии оставить сильными)

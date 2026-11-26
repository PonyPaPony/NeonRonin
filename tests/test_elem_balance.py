import pytest, json
from conftest import js, run

BUILDS = {
    'мета: крит+гром+вамп': ["{id:'crit',t:4,v:16,v2:70}", "{id:'chain',t:4,v:23}", "{id:'vamp',t:4,v:7}"],
    'огонь+крит+вамп':      ["{id:'burn',t:4,v:24}", "{id:'crit',t:4,v:16,v2:70}", "{id:'vamp',t:4,v:7}"],
    'яд+крит+вамп':         ["{id:'poison',t:4,v:23}", "{id:'crit',t:4,v:16,v2:70}", "{id:'vamp',t:4,v:7}"],
    'лёд+крит+вамп':        ["{id:'frost',t:4,v:20}", "{id:'crit',t:4,v:16,v2:70}", "{id:'vamp',t:4,v:7}"],
    'огонь+яд+крит':        ["{id:'burn',t:4,v:24}", "{id:'poison',t:4,v:23}", "{id:'crit',t:4,v:16,v2:70}"],
    'гром+яд+крит':         ["{id:'chain',t:4,v:23}", "{id:'poison',t:4,v:23}", "{id:'crit',t:4,v:16,v2:70}"],
    'лёд+гром+крит':        ["{id:'frost',t:4,v:20}", "{id:'chain',t:4,v:23}", "{id:'crit',t:4,v:16,v2:70}"],
    'огонь+лёд+крит':       ["{id:'burn',t:4,v:24}", "{id:'frost',t:4,v:20}", "{id:'crit',t:4,v:16,v2:70}"],
}
SETUP = "runCmd('unlock3'); runCmd('rank_weapon 12'); runCmd('rank_armor 12'); S.w.lvl = 8; S.a.lvl = 8; for (const s of SOUL) S.soul[s.id] = SOUL_MAX; travelTo(3); fixSlots(); refreshStats(); G.god = true;"


def measure(page, ench, secs=6, speed=3):
    run(page, f"S.w.ench = [{', '.join(ench)}, null]; refreshStats(); G.dsess = null; G.dummy.hp = G.dummy.maxHp; G.dummy.st = null; hero.x = DUMMY.x - 60; hero.y = DUMMY.y; G.speed = {speed};")
    page.wait_for_timeout(secs * 1000)
    r = js(page, "(() => { const s = G.dsess; const t = Math.max(0.1, (s.done ? s.end : G.time) - s.t0); G.speed = 1; return s.sum / t; })()")
    page.wait_for_timeout(2500)   # отойти/сбросить замер
    run(page, "hero.x = DUMMY.x - 600; G.dsess = null;"); page.wait_for_timeout(2300)
    return r


@pytest.mark.slow
def test_elem_balance_dummy(page):
    run(page, SETUP); page.wait_for_timeout(1500)
    res = {}
    for name, ench in BUILDS.items():
        res[name] = sorted(measure(page, ench) for _ in range(2))[-1]
    best = max(res.values())
    print(json.dumps({k: round(v / best, 3) for k, v in res.items()}, ensure_ascii=False))
    # одиночная цель: гром без соседей не работает — старая мета (крит+гром+вамп) здесь закономерно ниже; её проверяет авто-охота
    assert min(v for k, v in res.items() if not k.startswith('мета')) >= 0.75 * best   # шум замера ±10%; молния по одинокой цели подняла билды с громом


@pytest.mark.slow
def test_elem_balance_autohunt(page):
    run(page, SETUP + " SET.autoBoss = false; G.autoBossTest = false;"); page.wait_for_timeout(1000)
    res = {}
    for name in ['мета: крит+гром+вамп', 'лёд+гром+крит', 'гром+яд+крит', 'огонь+лёд+крит', 'яд+крит+вамп']:
        run(page, f"S.w.ench = [{', '.join(BUILDS[name])}, null]; refreshStats(); hero.hp = ST.maxHp; runCmd('tp 2'); toggleAuto(true);")
        page.wait_for_timeout(3000); k0 = js(page, "S.kills"); run(page, "G.speed = 2;")
        page.wait_for_timeout(40000); res[name] = js(page, "S.kills") - k0; run(page, "G.speed = 1;")
    best = max(res.values())
    print(json.dumps(res, ensure_ascii=False))
    assert min(res.values()) >= 0.5 * best   # убийства в минуту сильно шумят (случайный спавн, лёд замедляет подход врагов)


def test_shell_survival(page):
    """Точная проверка: 400 одинаковых ударов по 5% HP (раз в 0,6 с; щит в бою не восстанавливается) с одинаковой последовательностью случайных чисел — сколько урона дошло до героини."""
    run(page, SETUP + " G.god = false; G.speed = 0.0001;")
    sets = {'без Панциря (уклонение+щит)': "{id:'dodge',t:4,v:14}, {id:'eshield',t:4,v:33}", 'Панцирь+уклонение': "{id:'shell',t:4,v:80}, {id:'dodge',t:4,v:14}", 'Панцирь+щит': "{id:'shell',t:4,v:80}, {id:'eshield',t:4,v:33}"}
    res = {}
    for name, a in sets.items():
        res[name] = js(page, f"""(() => {{ S.a.ench = [{a}, null, null]; refreshStats(); let seed = 12345; const r0 = Math.random; Math.random = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
          const foe = {{ x: hero.x + 40, y: hero.y, hp: 1e18, maxHp: 1e18, def: 0, eva: 0, st: null }}; let taken = 0; G.shellN = 0; G.shellT = 0; refreshStats(); hero.shield = ST.shieldMax || 0;
          for (let i = 0; i < 400; i++) {{ hero.hp = ST.maxHp; hero.dead = false; hero.iframe = 0; hero.dashT = 0; const h = hero.hp + hero.shield; damageHero(ST.maxHp * 0.05, foe); taken += Math.max(0, h - hero.hp - hero.shield); if (typeof shellTick === 'function') shellTick(0.6); }}
          Math.random = r0; return taken / ST.maxHp; }})()""")
    print(json.dumps({k: round(v, 2) for k, v in res.items()}, ensure_ascii=False))
    base = res['без Панциря (уклонение+щит)']
    assert res['Панцирь+уклонение'] <= 0.9 * base   # точный замер: ≈ −15% урона (щит в долгом бою срабатывает один раз)

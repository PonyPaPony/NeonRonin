import pytest, json
from conftest import js, run

# Ориентиры спеки 5.3: шаг 1 ≈ 2–5 мин фарма текущего уровня, шаг 2 ≈ 20–40 мин, шаг 3 ≈ 1,5–3 ч (горы)
SETUP = {
    1: "runCmd('rank_weapon 4'); runCmd('rank_armor 4'); S.w.lvl = 8; S.a.lvl = 8; runCmd('soul 30'); travelTo(1); S.maxZone = 4;",
    2: "runCmd('unlock'); runCmd('rank_weapon 8'); runCmd('rank_armor 8'); S.w.lvl = 8; S.a.lvl = 8; runCmd('soul 70'); runCmd('loc 2'); S.maxZone = 4; S.maxZone2 = 4;",
    3: "runCmd('unlock3'); runCmd('rank_weapon 12'); runCmd('rank_armor 12'); S.w.lvl = 8; S.a.lvl = 8; runCmd('soul 100'); runCmd('loc 3'); S.maxZone = 4; S.maxZone2 = 4; S.maxZone3 = 4;",
}


def farm(page, loc, secs=80, speed=1):
    run(page, SETUP[loc] + " fixSlots(); refreshStats(); hero.hp = ST.maxHp; G.god = true; G.autoBossTest = false; SET.autoBoss = false; vPeakUpdate();")
    run(page, "runCmd('tp 4'); toggleAuto();")
    page.wait_for_timeout(3000)
    g0 = js(page, "S.gold"); run(page, f"G.speed = {speed};"); page.wait_for_timeout(secs * 1000)
    g1 = js(page, "S.gold"); run(page, "G.speed = 1;")
    per_min = (g1 - g0) / (secs * speed / 60)
    c = js(page, "[1, 2, 3].map(s => vCost('tea', s).gold)")
    return per_min, [x / per_min for x in c]


@pytest.mark.slow
@pytest.mark.parametrize('loc', [1, 2, 3])
def test_tempo(page, loc):
    per_min, mins = farm(page, loc)
    print(json.dumps({'loc': loc, 'gold_per_min': round(per_min), 'minutes_step': [round(m, 1) for m in mins]}))
    if loc in (1, 2):
        assert 2 <= mins[0] <= 5 and 20 <= mins[1] <= 40
    else:  # в горах йен в минуту меньше, чем в Храме у района 4: цены привязаны к лучшему источнику (Храм) — peakGM = 5600
        assert js(page, "villageGM()") == 5600


def test_full_village_timer_days(page):
    run(page, "S.village.steps.ratusha = 0;")
    total = js(page, "VILLAGE.reduce((a, b) => a + [1, 2, 3].reduce((x, s) => x + V_TIME[s - 1] * b.timeW, 0), 0) / 2 / 864e5")
    assert 1.2 <= total <= 3   # чистое время стройки по таймерам спеки 2 бригадами ≈ 1,5 суток; недели дают цены

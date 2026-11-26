import pytest, json
from conftest import js, run
from test_village_tempo import SETUP


@pytest.mark.slow
@pytest.mark.parametrize('loc', [2, 3])
def test_star_tempo(page, loc):
    run(page, SETUP[loc] + " for (const s of SOUL) S.soul[s.id] = SOUL_MAX; fixSlots(); refreshStats(); hero.hp = ST.maxHp; G.god = true; G.autoBossTest = false; SET.autoBoss = false;")
    run(page, "runCmd('tp 4'); toggleAuto();"); page.wait_for_timeout(3000)
    x0 = js(page, "S.xp"); page.wait_for_timeout(80000); x1 = js(page, "S.xp")
    per_min = (x1 - x0) / (80 / 60)
    first = js(page, "starCost(0)") / per_min
    const10 = js(page, "Array.from({length: 10}, (_, i) => starCost(i)).reduce((a, b) => a + b, 0)") / per_min
    print(json.dumps({'loc': loc, 'xp_per_min': round(per_min), 'min_first_star': round(first, 1), 'min_first_constellation': round(const10, 1)}))

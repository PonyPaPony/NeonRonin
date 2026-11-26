from conftest import js, run, load_save, frames, travel

RICH = "S.gold = 1e12; S.souls = 1e6; S.jade = 1e6;"
CRYSTAL = "S.village.crystal = true;"


def test_needs_crystal(page):
    assert js(page, "vCanBuild('ratusha')")["why"] == "Нужен кристалл защиты"


def test_ratusha_gates_others(page):
    run(page, CRYSTAL + RICH)
    assert js(page, "vCanBuild('herald')")["why"] == "Сначала Ратуша: шаг 1"
    assert js(page, "vCanBuild('ratusha')")["ok"] is True


def test_ratusha2_needs_temple(page):
    run(page, CRYSTAL + RICH + "S.village.steps.ratusha = 1; S.unlock2 = false;")
    assert js(page, "vCanBuild('ratusha')")["why"] == "Откроется после Храмового квартала"
    run(page, "S.unlock2 = true; S.village.steps.ratusha = 2; S.unlock3 = false;")
    assert js(page, "vCanBuild('ratusha')")["why"] == "Откроется после Горного пика"


def test_max_and_money_reasons(page):
    run(page, CRYSTAL + "S.village.steps.ratusha = 3; S.gold = 0;")
    assert js(page, "vCanBuild('ratusha')")["why"] == "Уже на максимуме"
    assert js(page, "vCanBuild('tea')")["why"] == "Не хватает ¥"


def test_step3_needs_souls_jade(page):
    run(page, CRYSTAL + RICH + "S.village.steps.ratusha = 3; S.village.steps.tea = 2; S.souls = 0;")
    assert js(page, "vCanBuild('tea')")["why"] == "Не хватает ◆"
    run(page, "S.souls = 1e6; S.jade = 0;")
    assert js(page, "vCanBuild('tea')")["why"] == "Не хватает ✧"


def test_build_and_finish(page):
    p = page
    run(p, CRYSTAL + RICH)
    g0 = js(p, "S.gold"); c = js(p, "vCost('ratusha', 1)")
    assert js(p, "vStartBuild('ratusha')") is True
    assert js(p, "S.gold") == g0 - c["gold"]
    t = js(p, "vTime('ratusha', 1)")
    travel(p, t - 1000); run(p, "vTick();")
    assert js(p, "vStep('ratusha')") == 0
    travel(p, 2000); run(p, "vTick();")
    assert js(p, "vStep('ratusha')") == 1 and js(p, "S.village.queue") == []


def test_already_building(page):
    run(page, CRYSTAL + RICH + "vStartBuild('ratusha');")
    assert js(page, "vCanBuild('ratusha')")["why"] == "Уже строится"


def test_slots_1_then_2(page):
    run(page, CRYSTAL + RICH + "S.village.steps.ratusha = 1; vStartBuild('tea');")
    assert js(page, "vCanBuild('spring')")["why"] == "Нет свободной бригады"
    run(page, "S.village.steps.ratusha = 2;")
    assert js(page, "vCanBuild('spring')")["ok"] is True


def test_double_build_charges_once(page):  # Review Focus 4
    run(page, CRYSTAL + RICH)
    g0 = js(page, "S.gold")
    assert js(page, "[vStartBuild('ratusha'), vStartBuild('ratusha')]") == [True, False]
    assert js(page, "S.village.queue.length") == 1
    assert js(page, "S.gold") == g0 - js(page, "vCost('ratusha', 1).gold")


def test_offline_completion_in_order(page):  # Review Focus 1
    p = page
    run(p, CRYSTAL + RICH + "S.village.steps.ratusha = 2; vStartBuild('tea'); vStartBuild('spring'); save(); G.noSaveOnUnload = true;")
    travel(p, 10 * 3600 * 1000)
    p.reload(); p.wait_for_function("typeof S==='object' && S.village", polling=100, timeout=15000)
    assert js(p, "[vStep('tea'), vStep('spring'), S.village.queue.length]") == [1, 1, 0]
    run(p, "vTick(); vTick();")
    assert js(p, "[vStep('tea'), vStep('spring')]") == [1, 1]


def test_clock_back_caps_remaining(page):  # Review Focus 2
    run(page, CRYSTAL + RICH + "vStartBuild('ratusha'); S.village.queue[0].endTs = Date.now() + 30 * 864e5; vTick();")
    assert js(page, "S.village.queue[0].endTs - Date.now() <= vTime('ratusha', 1) + 50") is True


def test_ratusha3_speeds_timers(page):
    base = js(page, "vTime('tea', 2)")
    run(page, "S.village.steps.ratusha = 3;")
    assert abs(js(page, "vTime('tea', 2)") - base * 0.8) < 1


def test_times_in_ranges(page):
    r = js(page, "VILLAGE.map(b => [1, 2, 3].map(s => vTime(b.id, s) / 60000))")
    for t1, t2, t3 in r:
        assert 1 <= t1 <= 10 and 30 <= t2 <= 90 and 120 <= t3 <= 360


def test_costs_scale_with_peak(page, V6):
    load_save(page, V6)
    assert js(page, "vCost('tea', 1).gold") == round(1.0 * 2750 * 5600)
    assert js(page, "vCost('tea', 3)") == {"gold": round(132000 * 5600), "souls": 1500, "jade": 200}

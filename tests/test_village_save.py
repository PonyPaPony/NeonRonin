from conftest import js, run, load_save, IDS


def test_v6_save_gets_village(page, V6):
    load_save(page, V6)
    v = js(page, "S.village")
    assert v["shards"] == [False] * 4 and v["crystal"] is False  # intro ставится при показе приглашения (T2)
    assert all(v["steps"][i] == 0 for i in IDS) and v["queue"] == []
    assert v["peakGM"] == 5600


def test_village_table_ids(page):
    assert js(page, "VILLAGE.map(b => b.id)") == IDS
    assert js(page, "VILLAGE.filter(b => b.kind === 'existing').map(b => b.id)") == ['herald', 'forge', 'shop', 'nursery']


def test_peak_monotonic_after_oni(page, V6):
    load_save(page, V6)
    run(page, "S.village.steps.ratusha = 2; oniAwaken();")
    assert js(page, "S.village.peakGM") == 5600 and js(page, "S.village.steps.ratusha") == 2
    assert js(page, "villageGM()") == 5600


def test_peak_grows_with_new_zone(page):
    assert js(page, "S.village.peakGM") == 1
    run(page, "S.loc = 1; setMaxZone(3);")
    assert js(page, "S.village.peakGM") == 25


def test_import_v6_code(page, V6):  # Review Focus 3
    code = page.evaluate("async d => { const keep = S; S = d; const pr = makeSaveCode(); S = keep; save(); return await pr; }", V6)
    run(page, "toggleMenu(true);")
    page.fill('#mn-code', code)
    page.click('#menu [data-act="import"]')
    with page.expect_navigation():
        page.click('#menu [data-act="import"]')
    page.wait_for_function("typeof S==='object' && typeof hero==='object' && S.village", polling=100, timeout=15000)
    assert js(page, "S.village.peakGM") == 5600
    assert js(page, "S.village.crystal") is False


def test_garbage_village_sanitized(page, V6):
    load_save(page, {**V6, "village": {"steps": {"ratusha": 9, "bogus": 2, "tea": -3}, "queue": "x", "shards": [1, 0], "peakGM": "zz"}})
    assert js(page, "S.village.steps.ratusha") == 3
    assert js(page, "'bogus' in S.village.steps") is False
    assert js(page, "S.village.steps.tea") == 0
    assert js(page, "S.village.queue") == []
    assert js(page, "S.village.shards") == [True, False, False, False]
    assert js(page, "S.village.peakGM") == 5600

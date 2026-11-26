import re
from conftest import js, run, frames


def setup(page, **kw):
    run(page, "S.village.crystal = true; " + " ".join(f"S.village.steps.{k} = {v};" for k, v in kw.items()) + " refreshStats();")


def test_resident_appears_with_step(page):
    setup(page, tea=0)
    assert 'ota' not in js(page, "vResidents().map(r => r.id)")
    setup(page, tea=1)
    assert 'ota' in js(page, "vResidents().map(r => r.id)")


def test_no_residents_without_crystal(page):
    run(page, "S.village.steps.tea = 3;")
    assert js(page, "vResidents().length") == 0


def test_near_bubble_from_pool(page):
    setup(page, tea=1)
    r = js(page, "vResidents().find(r => r.id === 'ota')")
    run(page, f"hero.x = {r['x']} + 40; hero.y = {r['y']} + 20; G.vBubble = null;"); frames(page, 6)
    b = js(page, "G.vBubble")
    assert b and b["id"] == "ota" and b["text"] in js(page, "VLINES.ota.near.concat(VLINES.ota.morning, VLINES.ota.evening)")


def test_near_bubble_cooldown(page):
    setup(page, tea=1)
    r = js(page, "vResidents().find(r => r.id === 'ota')")
    run(page, f"hero.x = {r['x']} + 40; hero.y = {r['y']} + 20; G.vBubble = null;"); frames(page, 6)
    run(page, "G.vBubble = null;"); frames(page, 30)
    assert js(page, "G.vBubble") is None


def test_herald_lines_on_take_claim(page):
    setup(page, ratusha=1, herald=1)
    run(page, "S.quests.active = []; S.quests.offers = []; ensureOffers(); G.boardTab = 'offers'; openBoard();")
    assert "Глашатай Тэцу" in page.inner_text('#board')
    page.click('#board [data-act="accept"]:not([data-kind="trial"])')
    assert js(page, "G.vHeraldLine") in js(page, "VLINES.tetsu.take")
    assert js(page, "G.vHeraldLine") in page.inner_text('#board')
    run(page, "S.quests.active[0].done = true; renderBoard();")
    page.click('#board [data-act="claim"]')
    assert js(page, "G.vHeraldLine") in js(page, "VLINES.tetsu.claim")


def test_board_unchanged_without_herald(page):
    run(page, "openBoard();")
    assert "Глашатай Тэцу" not in page.inner_text('#board')


def test_lowhp_return(page):
    setup(page, ratusha=1, tea=1, forge=1)
    run(page, "runCmd('tp 1');"); frames(page, 5)
    run(page, "hero.hp = ST.maxHp * 0.2; G.vBubble = null; hero.x = 900; hero.y = 1700;"); frames(page, 5)
    b = js(page, "G.vBubble")
    assert b and b["text"] in js(page, f"VLINES['{b['id']}'].lowhp")


def test_event_lines(page):
    setup(page, ratusha=1, forge=1)
    run(page, "G.vBubble = null; vEvent('built', 'forge');")
    b = js(page, "G.vBubble")
    assert b["id"] == "kami" and b["text"] in js(page, "VLINES.kami.built")
    run(page, "G.vBubble = null; vEvent('rank');")
    assert js(page, "G.vBubble.text") in js(page, f"VLINES[G.vBubble.id].rank")


def test_lines_count(page):
    bad = js(page, """Object.entries(VLINES).flatMap(([id, L]) => { const all = Object.values(L).flat(); const r = [];
        if (all.length < 8) r.push(id + ': мало реплик ' + all.length);
        for (const s of all) if (!s || /[A-Za-z]/.test(s)) r.push(id + ': ' + s); return r; })""")
    assert bad == []
    assert sorted(js(page, "Object.keys(VLINES)")) == sorted(js(page, "Object.keys(VRES)"))


def test_residents_drawn(page):
    setup(page, ratusha=3, tea=3, forge=3, shop=3, herald=3, nursery=3, spring=3, shrine=3, house1=3, house2=3, tower1=3)
    run(page, "hero.x = 500; hero.y = 1100;"); frames(page, 20)
    assert js(page, "G.vResDrawn") > 0

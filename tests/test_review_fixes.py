from conftest import js, run, frames


def test_board_texts_follow_active_max(page):
    run(page, "S.village.crystal = true; S.village.steps.ratusha = 2; S.village.steps.herald = 2; S.quests.active = []; G.boardTab = 'offers'; openBoard();")
    t = page.inner_text('#board')
    assert "до четырёх" in t and "до трёх" not in t
    run(page, "S.quests.active = [genQuest(), genQuest(), genQuest(), genQuest()]; renderBoard();")
    title = js(page, "document.querySelector('#board [data-act=\"accept\"][data-kind=\"order\"]').title")
    assert title == "Можно держать не больше 4 заданий"


def test_tree_hidden_flag_cached_per_location(page):
    for loc in (1, 2, 3):
        run(page, f"runCmd('unlock3'); travelTo({loc});")
        assert js(page, "WORLD.trees.every(o => o.vHid === (o.x < baseW() && !!vPlotAt(o.x, o.y)))") is True
        assert js(page, "WORLD.trees.filter(o => o.vHid).length") > 0


def test_residents_list_cached_until_steps_change(page):
    run(page, "S.village.crystal = true; S.village.steps.tea = 1;")
    a = js(page, "vResidents() === vResidents()")
    assert a is True
    run(page, "S.village.steps.spring = 1;")
    assert 'zen' in js(page, "vResidents().map(r => r.id)")

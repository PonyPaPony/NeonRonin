from conftest import js, run, frames, load_save

VIS = "!document.querySelector('#village').classList.contains('hidden')"


def to(page, x, y):
    run(page, f"hero.x = {x}; hero.y = {y};"); frames(page, 4)


def test_open_from_ratusha_circle(page):
    to(page, 500, 1960)
    assert js(page, VIS) is False
    to(page, js(page, "RATUSHA.x"), js(page, "RATUSHA.y"))
    assert js(page, VIS) is True
    to(page, 500, 1960)
    assert js(page, VIS) is False


def test_circle_no_reopen_loop(page):  # Review Focus 5
    to(page, js(page, "RATUSHA.x"), js(page, "RATUSHA.y"))
    page.keyboard.press('Escape')
    frames(page, 30)
    assert js(page, VIS) is False
    to(page, 500, 1960); to(page, js(page, "RATUSHA.x"), js(page, "RATUSHA.y"))
    assert js(page, VIS) is True


def test_ratusha_away_from_base_objects(page):
    bad = js(page, """[FORGE, BOARD, SHOP, NURSERY, PORTAL].filter(o => Math.hypot(o.x - RATUSHA.x, o.y - RATUSHA.y) < o.r + RATUSHA.r + 20).length
        + (Math.hypot(DUMMY.x - RATUSHA.x, DUMMY.y - RATUSHA.y) < RATUSHA.r + 60 ? 1 : 0) + (Math.hypot(SPAWN.x - RATUSHA.x, SPAWN.y - RATUSHA.y) < RATUSHA.r + 40 ? 1 : 0)""")
    assert bad == 0 and js(page, "RATUSHA.x < baseW() - RATUSHA.r") is True


def test_open_from_menu_and_V(page):
    run(page, "toggleMenu(true);")
    page.click('#menu [data-act="village"]')
    assert js(page, VIS) is True and js(page, "G.menuOpen") is False
    page.keyboard.press('Escape'); frames(page, 2)
    assert js(page, VIS) is False
    page.keyboard.press('KeyV'); frames(page, 2)
    assert js(page, VIS) is True
    page.keyboard.press('KeyV'); frames(page, 2)
    assert js(page, VIS) is False


def test_tower_blocks_window(page, V6):
    load_save(page, V6)
    run(page, "towerEnter(1, 1);"); frames(page, 3)
    page.keyboard.press('KeyV'); frames(page, 2)
    assert js(page, VIS) is False
    assert "Деревня осталась снаружи башни" in page.inner_text('#toasts')


def test_build_click(page):
    run(page, "S.village.crystal = true; S.gold = 1e9; openVillage();")
    page.click('#vl-map [data-act="vsel"][data-id="ratusha"]')
    page.click('#vl-card [data-act="vbuild"]')
    assert js(page, "S.village.queue.length") == 1
    assert "Ратуша" in page.inner_text('#vl-queue')
    assert ":" in page.inner_text('#vl-queue')


def test_disabled_shows_reason(page):
    run(page, "S.village.crystal = true; S.gold = 1e9; openVillage();")
    page.click('#vl-map [data-act="vsel"][data-id="herald"]')
    assert js(page, "document.querySelector('#vl-card [data-act=\"vbuild\"]').disabled") is True
    assert "Сначала Ратуша: шаг 1" in page.inner_text('#vl-card')


def test_card_lists_three_steps(page):
    run(page, "S.village.crystal = true; S.village.steps.ratusha = 1; S.village.steps.forge = 1; openVillage();")
    page.click('#vl-map [data-act="vsel"][data-id="forge"]')
    t = page.inner_text('#vl-card')
    assert "Кузнец Ками" in t and "−8%" in t and "−16%" in t and "−25%" in t


def test_no_crystal_view(page):
    run(page, "vOnShard(2); openVillage();")
    assert "Осколки кристалла: 1/4" in page.inner_text('#village')
    assert js(page, "document.querySelectorAll('#vl-map [data-act=\"vsel\"]').length") == 0

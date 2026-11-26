from conftest import js, run, frames

FULL = "for (const s of SOUL) S.soul[s.id] = SOUL_MAX;"


def test_buttons_only_when_full(page):
    run(page, FULL + " S.soul.pow = 19; toggleSoul(true);")
    assert js(page, "document.querySelectorAll('#soul [data-act=\"star\"]').length") == 0
    run(page, "S.soul.pow = 20; renderSoul();")
    assert js(page, "document.querySelectorAll('#soul [data-act=\"star\"]').length") == 8


def test_buy_one(page):
    run(page, FULL + " S.xp = 1e8; toggleSoul(true);")
    x0 = js(page, "S.xp")
    page.click('#soul [data-act="star"][data-id="pow"]')
    assert js(page, "[S.stars.b.pow, S.stars.peak, S.stars.spent]") == [1, 1, 1200000]
    assert js(page, "S.xp") == x0 - 1200000


def test_buy_max_stops(page):
    run(page, FULL + " S.xp = 1e30; toggleSoul(true);")
    page.click('#soul [data-act="starmax"][data-id="vit"]')
    n = js(page, "S.stars.b.vit")
    assert 1 <= n <= 1000


def test_buy_max_spends_until_short(page):
    run(page, FULL + " S.xp = starCost(0) + starCost(1) + 5; toggleSoul(true);")
    page.click('#soul [data-act="starmax"][data-id="agi"]')
    assert js(page, "[S.stars.b.agi, S.xp]") == [2, 5]


def test_constellation_banner(page):
    run(page, FULL + " S.xp = 1e12; S.stars.b.pow = 9; S.stars.peak = 9; toggleSoul(true);")
    page.click('#soul [data-act="star"][data-id="pow"]')
    assert "Созвездие 1" in js(page, "G.banner.text")


def test_counts_and_price_text(page):
    run(page, FULL + " S.xp = 1e8; S.stars.b.fury = 1; S.stars.peak = 1; toggleSoul(true);")
    assert "★1" in page.inner_text('#soul')
    assert "следующая звезда" in page.inner_text('#s-sub')


def test_no_stars_in_tower(page, V6):
    from conftest import load_save
    load_save(page, V6)
    run(page, FULL + " save(); towerEnter(1, 1); toggleSoul(true);")
    assert js(page, "document.querySelectorAll('#soul [data-act=\"star\"]').length") == 0


def test_card_and_summary_show_star_effect(page):
    run(page, FULL + " S.stars.b.pow = 3; S.stars.peak = 3; toggleSoul(true);")
    assert "★ +6% урона" in page.inner_text('#s-grid')
    assert "+126%" in page.inner_text('#s-sum')

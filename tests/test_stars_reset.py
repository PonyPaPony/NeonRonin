from conftest import js, run

FULL = "for (const s of SOUL) S.soul[s.id] = SOUL_MAX;"


def buy(page, n, id='pow'):
    run(page, FULL + f" S.xp = 1e12; for (let i = 0; i < {n}; i++) starBuy('{id}');")


def test_reset_refunds_all(page):
    buy(page, 5)
    spent, xp0 = js(page, "[S.stars.spent, S.xp]")
    run(page, "S.gold = 0; openShop();")
    page.click('#shop [data-act="starreset"]'); page.click('#shop [data-act="starreset"]')
    assert js(page, "S.xp") == xp0 + spent
    assert js(page, "[starsTotal(), S.stars.spent, S.stars.resets, S.gold]") == [0, 0, 1, 0]


def test_reset_price_doubles(page):
    g = js(page, "shopGM()")
    for r, k in [(1, 1), (3, 4), (9, 16)]:
        run(page, f"S.stars.resets = {r};")
        assert js(page, "starResetPrice()") == round(600 * g * k)


def test_reset_needs_confirm(page):
    buy(page, 2)
    run(page, "openShop();")
    page.click('#shop [data-act="starreset"]')
    assert js(page, "starsTotal()") == 2
    assert "Точно сбросить?" in page.inner_text('#shop [data-act="starreset"]')
    page.wait_for_timeout(3300)
    assert "Сбросить звёзды" in page.inner_text('#shop [data-act="starreset"]')


def test_reset_disabled_without_stars(page):
    run(page, FULL + " S.gold = 1e9; S.stars.resets = 2; openShop();")
    assert js(page, "document.querySelector('#shop [data-act=\"starreset\"]').disabled") is True
    g = js(page, "S.gold"); run(page, "doStarReset(); doStarReset();")
    assert js(page, "S.gold") == g


def test_constellations_survive_reset(page):
    buy(page, 20)
    run(page, "refreshStats();"); d = js(page, "constN()")
    run(page, "doStarReset(); doStarReset(); refreshStats();")
    assert d == 2 and js(page, "constN()") == 2 and js(page, "starsTotal()") == 0


def test_reset_hidden_before_full_soul(page):
    run(page, "openShop();")
    assert js(page, "document.querySelector('#shop [data-act=\"starreset\"]')") is None

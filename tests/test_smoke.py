from conftest import _open
def test_smoke_orig(browser, srv_orig):
    ctx, page = _open(browser, srv_orig); page.wait_for_timeout(1500); errs = page.errors; ctx.close(); assert errs == []
def test_smoke_www(page):
    page.wait_for_timeout(1500)

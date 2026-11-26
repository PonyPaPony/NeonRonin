import os
import json, os, threading, functools, http.server, socketserver, pytest
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures')
IDS = ['ratusha', 'herald', 'forge', 'shop', 'nursery', 'tea', 'spring', 'shrine',
       'house1', 'house2', 'house3', 'house4', 'palisade', 'tower1', 'tower2']


def _serve(path):
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Q, directory=path)
    s = socketserver.ThreadingTCPServer(('127.0.0.1', 0), h)
    s.daemon_threads = True
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


@pytest.fixture(scope='session')
def srv():
    s = _serve(os.path.join(ROOT, 'www'))
    yield f'http://127.0.0.1:{s.server_address[1]}/index.html'
    s.shutdown()


@pytest.fixture(scope='session')
def srv_orig():
    s = _serve(os.path.join(ROOT, 'orig'))
    yield f'http://127.0.0.1:{s.server_address[1]}/index.html'
    s.shutdown()


@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as p:
        exe = os.environ.get('CHROME') or ('/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)   # иначе — Chromium из Playwright
        b = p.chromium.launch(executable_path=exe, args=['--autoplay-policy=no-user-gesture-required'])
        yield b
        b.close()


TIME_SHIM = "(() => { const n = Date.now.bind(Date), O = Date; const off = () => +(localStorage.getItem('__off') || 0); Date.now = () => n() + off(); })();"


def travel(page, ms):
    """Сдвинуть часы страницы (Date.now) вперёд/назад; сдвиг переживает перезагрузку."""
    page.evaluate("ms => localStorage.setItem('__off', String((+localStorage.getItem('__off') || 0) + ms))", ms)


def _open(browser, url, viewport=None, **kw):
    ctx = browser.new_context(service_workers='block', viewport=viewport or {'width': 1280, 'height': 720}, **kw)
    ctx.add_init_script(TIME_SHIM)
    page = ctx.new_page()
    page.errors = []
    page.on('pageerror', lambda e: page.errors.append(str(e)))
    page.goto(url)
    page.wait_for_function("typeof S==='object' && typeof G==='object' && typeof hero==='object'", polling=100, timeout=15000)
    return ctx, page


@pytest.fixture
def page(browser, srv):
    ctx, page = _open(browser, srv)
    yield page
    errs = list(page.errors)
    ctx.close()
    assert errs == [], errs


@pytest.fixture
def open_page(browser, srv):
    """Фабрика: открыть страницу с особыми параметрами контекста (часы, телефон)."""
    made = []
    def mk(**kw):
        ctx, p = _open(browser, srv, **kw)
        made.append((ctx, p))
        return p
    yield mk
    for ctx, p in made:
        errs = list(p.errors); ctx.close()
        assert errs == [], errs


def js(page, expr):
    return page.evaluate(f"() => {{ return ({expr}); }}") if not expr.strip().startswith('{') else page.evaluate(expr)


def run(page, code):
    page.evaluate(f"() => {{ {code} }}")


def load_save(page, data):
    page.evaluate("d => { G.noSaveOnUnload = true; localStorage.setItem(CFG.SAVE_KEY, JSON.stringify(d)); }", data)
    page.reload()
    page.wait_for_function("typeof S==='object' && typeof G==='object' && typeof hero==='object'", polling=100, timeout=15000)


def frames(page, n=10):
    page.evaluate(f"() => new Promise(r => {{ let k = {n}; const f = () => (--k <= 0 ? r() : requestAnimationFrame(f)); requestAnimationFrame(f); }})")


@pytest.fixture(scope='session')
def V6():
    with open(os.path.join(FIX, 'save_v6.json'), encoding='utf-8') as f:
        return json.load(f)

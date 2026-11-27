"""Замер билда: кнопка фиксирует билд и урон за N секунд и скачивает файл."""
import json
from conftest import js, run

BASE = ("runCmd('открыть всё'); runCmd('soul 100'); travelTo(3); fixSlots(); S.w.rank = 12; S.w.ench = [{id:'burn', t:5, v:36}, {id:'crit', t:4, v:12}, null, null];"
        "S.runes.w[0] = {id:'elem', r:3, f:[0,0,0,0,0,0]}; refreshStats(); G.god = true;")
HITS = "(() => { const d = G.dummy; d.hp = d.maxHp = 1e15; d.eva = 0; for (let i = 0; i < %d; i++) dealDamage(d, 100); })()"


def test_zamer_waits_for_first_hit_and_finishes(page):
    run(page, BASE + "runCmd('замер 2');")
    assert js(page, "G.zm && G.zm.t0 === null") is True
    assert '📊' in page.inner_text('#zamer-tag')
    page.wait_for_timeout(400)
    assert js(page, "G.zm.t0 === null") is True                     # без ударов отсчёт не идёт
    with page.expect_download(timeout=8000) as dl:
        run(page, HITS % 20 + ";")
        run(page, "G.time += 2.2;")
    path = dl.value.path(); name = dl.value.suggested_filename
    assert name.startswith('neonronin-zamer-') and name.endswith('.txt')
    txt = open(path, encoding='utf-8').read()
    assert 'Замер билда' in txt and 'Урон: среднее' in txt and 'пик за 1 с' in txt and 'пик за 5 с' in txt
    assert 'Ожог V' in txt and 'Стихия' in txt
    data = json.loads(txt.split('---JSON---', 1)[1])
    assert data['dur'] == 2 and data['total'] > 0 and data['hits'] >= 20
    assert data['build']['w']['rank'] == 12 and data['build']['runes']['w'][0]['id'] == 'elem'
    assert 'dmg' in data['stats'] and data['src']
    assert js(page, "G.zm") is None and js(page, "document.querySelector('#zamer-tag').classList.contains('hidden')") is True


def test_zamer_peaks_and_sources(page):
    run(page, BASE + "runCmd('замер 10');")
    r = js(page, """(() => { zamerStart(10); const d = G.dummy; d.hp = d.maxHp = 1e15; const t0 = G.time;
      for (let s = 0; s < 10; s++) { G.time = t0 + s; zamerHit(d, 'katana', s === 3 ? 1000 : 10, false); zamerHit(d, 'fire', 5, false); }
      const z = zamerResult(); return [z.total, z.peak1, z.peak5, z.avg, z.src.katana, z.src.fire]; })()""")
    assert r[0] == 1090 + 50
    assert r[1] == 1005                                               # всплеск за 1 с
    assert r[2] == (1000 + 4 * 10 + 5 * 5) / 5                       # лучшее окно 5 с: всплеск + 4 удара катаны + 5 тиков огня, в уроне за секунду
    assert abs(r[3] - 114) < 1e-6


def test_zamer_aborts_on_death(page):
    run(page, BASE + "runCmd('замер 30');")
    with page.expect_download(timeout=8000) as dl:
        run(page, HITS % 3 + "; G.god = false; heroDie();")
    txt = open(dl.value.path(), encoding='utf-8').read()
    assert 'прерван' in txt


def test_zamer_button_in_panel(page):
    run(page, "SET.console = true; toggleConsole(true);")
    assert js(page, "!!document.querySelector(\"#console [data-cmd='замер']\")") is True

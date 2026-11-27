"""Замер билда, доработка: урон по боссу и время победы, среднее «в бою», автостоп после босса, русские имена врагов."""
import json
from conftest import js, run

BASE = "runCmd('открыть всё'); runCmd('soul 100'); travelTo(3); fixSlots(); refreshStats(); G.god = true; S.pets.active = null; refreshPetFx();"


def test_boss_time_and_combat_avg(page):
    run(page, BASE + "runCmd('замер 60');")
    r = js(page, """(() => { const b = makeBoss(1); b.hp = b.maxHp = 1e15; const m = makeEnemy('bruiser', hero.x + 300, hero.y, 1, false); const t0 = G.time;
      zamerHit(m, 'katana', 100, false); G.time = t0 + 2; zamerHit(b, 'katana', 500, false); G.time = t0 + 3; zamerHit(b, 'fire', 500, false);
      G.time = t0 + 6.5; zamerHit(b, 'katana', 1000, false); return zamerResult(); })()""")
    assert r['boss']['dmg'] == 2000 and abs(r['boss']['time'] - 4.5) < 1e-6 and r['boss']['kill'] is None
    assert r['active'] == 4 and abs(r['avgCombat'] - 2100 / 4) < 1e-6


def test_autostop_after_boss_kill(page):
    run(page, BASE + "runCmd('замер 60');")
    with page.expect_download(timeout=10000) as dl:
        run(page, "const b = makeBoss(1); G.enemies.push(b); b.hp = b.maxHp = 5000; zamerHit(b, 'katana', 1000, false); G.time += 1.5; b.hp = 0; zamerHit(b, 'katana', 4000, false); killEnemy(b);")
        assert js(page, "G.zm && G.zm.stopAt > 0") is True
        run(page, "G.time += 3.2;")
    txt = open(dl.value.path(), encoding='utf-8').read()
    head, body = txt.split('---JSON---', 1)
    assert 'прерван' not in head and 'Босс:' in head and 'победа за 1.5 с' in head and 'в бою' in head
    d = json.loads(body)
    assert abs(d['boss']['kill'] - 1.5) < 1e-6 and d['boss']['dmg'] == 5000


def test_enemy_names_russian(page):
    run(page, BASE + "runCmd('замер 60');")
    r = js(page, "(() => { const m = makeEnemy('bruiser', hero.x + 300, hero.y, 1, false); zamerHit(m, 'katana', 10, false); return Object.keys(G.zm.tgt); })()")
    assert r and all(not k.isascii() for k in r)

from conftest import js, run, load_save, frames, travel

def steps(page, **kw):
    run(page, "S.village.crystal = true; " + " ".join(f"S.village.steps.{k} = {v};" for k, v in kw.items()) + " refreshStats();")


def base_stats(page):
    return js(page, "({ hp: ST.maxHp, dmg: ST.dmg, gold: ST.goldMul, xp: ST.xpMul, regen: ST.regen })")


def test_forge_discount(page):
    steps(page, forge=3)
    assert js(page, "towerCost(1000, 100, 10)") == [750, 75, 8]
    steps(page, forge=1)
    assert js(page, "towerCost(1000, 100, 10)") == [920, 92, 10]


def test_shop_discount(page):
    p0 = js(page, "itemPrice('potion')")
    steps(page, shop=2)
    assert js(page, "itemPrice('potion')") == round(p0 * 0.85)


def test_board_offers_active(page):
    run(page, "S.quests.offers = []; ensureOffers();")
    assert js(page, "S.quests.offers.length") == 4
    steps(page, herald=2)
    run(page, "ensureOffers();")
    assert js(page, "S.quests.offers.length") == 5
    assert js(page, "vActiveMax()") == 4
    run(page, "openBoard(); S.quests.active = [genQuest(), genQuest(), genQuest()]; G.boardTab = 'offers'; renderBoard();")
    page.click('#board [data-act="accept"][data-kind="offer"], #board [data-act="accept"]:not([data-kind="trial"])')
    assert js(page, "S.quests.active.length") == 4


def test_board_reward_mul(page):
    steps(page, herald=3)
    run(page, "const q = genQuest(); q.done = true; q.gold = 1000; q.souls = 0; q.xp = 0; q.jade = 0; S.quests.active = [q]; S.gold = 0; openBoard(); renderBoard();")
    page.click('#board [data-act="claim"]')
    assert js(page, "S.gold") == 1150


def test_pet_xp(page):
    run(page, "S.pets.owned.cat = S.pets.owned.cat || { lvl: 1, xp: 0 }; S.pets.owned.cat.lvl = 1; S.pets.owned.cat.xp = 0;")
    steps(page, nursery=3)
    run(page, "petGainXp(1, 'cat');")
    assert abs(js(page, "S.pets.owned.cat.xp + (S.pets.owned.cat.lvl - 1) * 1e9") - 1.5) < 1e-6


def test_houses_and_towers(page):
    b = base_stats(page)
    steps(page, house1=3, house2=1, tower1=3, tower2=2)
    s = base_stats(page)
    assert abs(s["gold"] - b["gold"] * 1.12) < 1e-9 and abs(s["xp"] - b["xp"] * 1.12) < 1e-9
    assert abs(s["hp"] - b["hp"] * 1.15) < 1e-6


def test_spring_regen_and_potion(page):
    b = base_stats(page)
    steps(page, spring=3)
    assert abs(js(page, "ST.regen") - (b["regen"] + 0.002 * js(page, "ST.healMul"))) < 1e-12
    got = js(page, "(() => { S.inv.potion = 1; G.potionCd = 0; hero.hp = 1; useItem('potion'); return hero.hp - 1 - ST.maxHp * 0.5; })()")
    assert abs(got) < 1e-6


def test_palisade_reduce(page):
    steps(page, palisade=3)
    got = js(page, "(() => { G.god = false; hero.iframe = 0; hero.dashT = 0; hero.shield = 0; ST.dodge = 0; ST.block = 0; ST.reduce = 0; ST.res = {}; hero.hp = ST.maxHp; const h0 = hero.hp; damageHero(100); return h0 - hero.hp; })()")
    assert abs(got - 94) < 1e-6


def test_shrine_only_random(page):
    steps(page, shrine=3)
    assert js(page, "ST.vDrop") == 2
    # обычный моб: Math.random = 0.04 → 0.04 < 0.025*luck*2 → ◆ выпадает только благодаря Святилищу
    got = page.evaluate("""() => { G.loot.length = 0; const e = G.enemies.find(x => !x.boss && !x.dead && !x.dummy) || null; if (!e) return 'none';
        e.elite = false; const r = Math.random; Math.random = () => 0.04; try { killEnemy(e); } finally { Math.random = r; } return G.loot.filter(l => l.type === 'soul').length; }""")
    if got == 'none':
        run(page, "runCmd('tp 1');"); frames(page, 30)
        got = page.evaluate("""() => { G.loot.length = 0; const e = G.enemies.find(x => !x.boss && !x.dead && !x.dummy); e.elite = false; const r = Math.random; Math.random = () => 0.04; try { killEnemy(e); } finally { Math.random = r; } return G.loot.filter(l => l.type === 'soul').length; }""")
    assert got == 1
    # босс: ◆ всё равно min(souls,10) штук, не больше
    b = page.evaluate("""() => { G.loot.length = 0; const b = makeBoss(1); G.enemies.push(b); killEnemy(b); return [G.loot.filter(l => l.type === 'soul').length, Math.min(b.souls, 10)]; }""")
    assert b[0] == b[1]


def test_tea_on_leaving_base(page):
    steps(page, tea=1)
    d0 = js(page, "ST.dmg")
    run(page, f"runCmd('tp 0');"); frames(page, 5)
    run(page, "hero.x = 1200; hero.y = CFG.WORLD_H / 2;"); frames(page, 5)
    assert 595 <= js(page, "G.teaT") <= 600
    assert abs(js(page, "ST.dmg") - d0 * 1.05) < 1e-6
    run(page, "G.teaT = 0.01;"); frames(page, 5)
    assert abs(js(page, "ST.dmg") - d0) < 1e-6


def test_tea_step3_longer(page):
    steps(page, tea=3)
    run(page, "runCmd('tp 0');"); frames(page, 5)
    run(page, "hero.x = 1200; hero.y = CFG.WORLD_H / 2;"); frames(page, 5)
    assert 895 <= js(page, "G.teaT") <= 900


def test_gift_once_per_day(page):
    steps(page, shop=1)
    run(page, "S.inv.potion = 0; S.inv.talisman = 0; S.inv.stone = 0;")
    run(page, "openShop(); closeShop(); openShop(); closeShop();")
    assert js(page, "S.inv.potion + S.inv.talisman") == 1
    travel(page, 86400e3)
    run(page, "openShop(); closeShop();")
    assert js(page, "S.inv.potion + S.inv.talisman") == 2 and js(page, "S.inv.stone") == 0


def test_gift_step3_adds_stone(page):
    steps(page, shop=3)
    run(page, "S.inv.stone = 0; openShop(); closeShop();")
    assert js(page, "S.inv.stone") == 1


def test_no_bonus_in_tower(page, V6):
    load_save(page, V6)
    b = base_stats(page)
    steps(page, **{k: 3 for k in ['forge', 'shop', 'herald', 'nursery', 'tea', 'spring', 'shrine', 'house1', 'palisade', 'tower1']})
    assert js(page, "ST.maxHp") > b["hp"]
    run(page, "towerEnter(1, 1); refreshStats();")
    assert js(page, "towerIn()") is True
    assert js(page, "vBonus('forgeDisc')") == 0 and js(page, "vBonus('hp')") == 0 and js(page, "ST.vReduce || 0") == 0
    run(page, "towerExit && towerExit(); refreshStats();")

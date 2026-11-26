# Тесты «Неонового Ронина»

Автотесты игры: pytest + Playwright, открывают `www/index.html` в настоящем браузере.

## Запуск
```bash
pip install pytest playwright
python -m playwright install chromium      # один раз; или укажи свой Chrome: CHROME=/путь/к/chrome
python -m pytest tests -q                  # быстрые (~5 мин)
python -m pytest tests -m slow -s -q       # медленные замеры: баланс, темп, стенд билдов
```

## Что где
- `conftest.py` — фикстуры: `page` (игра в браузере), `js`/`run` (выполнить код в игре), `load_save`, `frames`, `travel` (сдвиг часов без `page.clock` — он подвешивает игровой цикл).
- `fixtures/save_v6.json` — сейв живой версии v6 (проверка загрузки старых сохранений).
- `test_village_*` — деревня; `test_stars_*` — звёзды души; `test_elem_*`, `test_luck_shell` — стихии, удача, Панцирь; `test_balance_fix` — «Острота», 4-й слот, Печать; `test_regression`, `test_smoke` — общие пути.
- `test_boss_builds.py` (медленный) — стенд «чучело как Ямамба»: урон билдов Они на 3-м боссе гор.
- `tools/check.sh` — извлечь скрипт из `www/index.html`, `node --check`, посчитать строки без CRLF; `tools/ed.py` — правки с сохранением CRLF.

"""Точечные правки index.html с сохранением CRLF. Использование: python3 tools/ed.py patchfile.py
patchfile определяет EDITS = [(old, new), ...]; '\n' в строках = перевод строки файла (CRLF)."""
import sys, runpy
F = 'www/index.html'
edits = runpy.run_path(sys.argv[1])['EDITS']
s = open(F, 'rb').read().decode('utf-8')
for i, (old, new) in enumerate(edits):
    o = old.replace('\r\n', '\n').replace('\n', '\r\n'); n = new.replace('\r\n', '\n').replace('\n', '\r\n')
    c = s.count(o)
    if c != 1: sys.exit(f'edit {i}: найдено {c} раз: {old[:80]!r}')
    s = s.replace(o, n)
open(F, 'wb').write(s.encode('utf-8'))
print('ok', len(edits))

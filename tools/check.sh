#!/bin/bash
# node --check извлечённого скрипта + проверка CRLF
cd /home/claude/nr
python3 - <<'P'
import re
s=open('www/index.html','rb').read().decode('utf-8')
m=re.findall(r'<script>(.*?)</script>', s, re.S)
open('/tmp/nr_script.js','w').write('\n'.join(m))
lf=s.count('\n')-s.count('\r\n'); print('scripts',len(m),'bare LF',lf)
P
node --check /tmp/nr_script.js && echo "node --check OK"
git diff --stat -- www/index.html | tail -1

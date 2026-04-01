import shutil
from pathlib import Path

APP = Path('app.py')
shutil.copy(APP, APP.with_suffix('.py.bak'))
c = APP.read_text(encoding='utf-8')

old = "            img_d.width, img_d.height = 100, 30"
new = "            img_d.width, img_d.height = 200, 60"

if old in c:
    c = c.replace(old, new)
    print('✅ Potpis "Odobrio" povećan na 200x60')
else:
    print('❌ Pattern nije pronađen')

APP.write_text(c, encoding='utf-8')

#!/usr/bin/env python3
"""
patch_emp_info.py — kopiraj patchirane fajlove na pravo mjesto
Pokretanje: cd ~/Projects/Softman_app && python patch_emp_info.py
"""
import shutil, os

BASE = os.path.expanduser('~/Projects/Softman_app')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

files = [
    (os.path.join(SCRIPT_DIR, 'app.py'),       os.path.join(BASE, 'app.py')),
    (os.path.join(SCRIPT_DIR, 'settings.html'), os.path.join(BASE, 'templates', 'settings.html')),
]

for src, dst in files:
    if not os.path.exists(src):
        print(f'❌ Nedostaje: {src}'); continue
    shutil.copy2(dst, dst + '.bak')
    shutil.copy2(src, dst)
    print(f'✅ {os.path.basename(dst)} → {dst}')

print('\nGotovo! Pokreni: python app.py')
print('Git: cd ~/Projects/Softman_app && git add . && git commit -m "feat: kontakt info zaposlenika, info popup" && git push origin main')

#!/usr/bin/env python3
"""Patch: dodaj /reports hub rutu u app.py"""
import os, shutil

BASE = os.path.expanduser('~/Projects/Softman_app')
APP  = os.path.join(BASE, 'app.py')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)
shutil.copy2(APP, os.path.join(BACKUP_DIR, 'app.py.bak_reports_hub'))
print('✅ Backup napravljen')

with open(APP, 'r', encoding='utf-8') as f:
    content = f.read()

NEW_ROUTE = '''
@app.route('/reports')
@require_perm('can_view_reports')
def reports_hub():
    return render_template('reports_hub.html', active='reports')

'''

# Ubaci prije postojeće /reports/ rute
anchor = "@app.route('/reports/popis-naloga')"
if '/reports\'' not in content and anchor in content:
    content = content.replace(anchor, NEW_ROUTE + anchor, 1)
    print('✅ /reports hub ruta dodana')
else:
    print('⚠️  Ruta već postoji ili anchor nije pronađen')

with open(APP, 'w', encoding='utf-8') as f:
    f.write(content)

print('Pokreni: python3 app.py')

#!/usr/bin/env python3
"""Popravak: SQL sintaksna greška u migraciji projekata."""
import os, shutil

BASE = os.path.expanduser('~/Projects/Softman_app')
APP  = os.path.join(BASE, 'app.py')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)
shutil.copy2(APP, os.path.join(BACKUP_DIR, 'app.py.bak_projects_sqlfix'))
print('✅ Backup napravljen')

with open(APP, 'r', encoding='utf-8') as f:
    content = f.read()

# Popravi ''active'' -> 'active' i ''#2d5986'' -> '#2d5986' u SQL migraciji
OLD = (
    "            status TEXT DEFAULT ''active'',\n"
    "            color TEXT DEFAULT ''#2d5986'',\n"
)
NEW = (
    "            status TEXT DEFAULT 'active',\n"
    "            color TEXT DEFAULT '#2d5986',\n"
)

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    print('✅ SQL sintaksa popravljena')
else:
    print('⚠️  Stari string nije pronađen — provjeri ručno')
    # Pokaži kontekst
    idx = content.find("status TEXT DEFAULT ''active''")
    if idx != -1:
        print(f'   Pronađeno na poziciji {idx}:')
        print(repr(content[idx-20:idx+60]))

with open(APP, 'w', encoding='utf-8') as f:
    f.write(content)

print('\nPokreni: python3 app.py')

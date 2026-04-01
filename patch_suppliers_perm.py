#!/usr/bin/env python3
"""
Patch: app.py — supplier POST/PUT/DELETE endpointi
Zamijeni is_admin provjeru s is_admin OR can_edit_invoices
"""
import shutil
from pathlib import Path

APP = Path('app.py')
shutil.copy(APP, APP.with_suffix('.py.bak'))
c = APP.read_text(encoding='utf-8')

OLD = "    if not user or not user.get('is_admin'):\n        return jsonify({'success': False, 'error': 'Nemate ovlasti za ovu akciju.'}), 403"
NEW = "    if not user or not (user.get('is_admin') or user.get('can_edit_invoices')):\n        return jsonify({'success': False, 'error': 'Nemate ovlasti za ovu akciju.'}), 403"

count = c.count(OLD)
if count == 3:
    c = c.replace(OLD, NEW)
    print(f'✅ Zamijenjeno {count} provjere — can_edit_invoices dodan uz is_admin')
else:
    print(f'❌ Očekivano 3 pojavljivanja, pronađeno {count}')
    exit(1)

APP.write_text(c, encoding='utf-8')
print('✅ Patch primijenjen!')

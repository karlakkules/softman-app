#!/usr/bin/env python3
"""
Precizni patch za sortiranje faktura u app.py.

Problem: ORDER BY i.invoice_date DESC ne radi jer datumi u bazi
nisu konzistentno ISO format (ima: 19.3.2026, 01.03.2026, 2026-03-19 itd.)
SQLite sortira te stringove leksikografski što daje krivi redosljed.

Rješenje: Dodati Python sort NAKON fetchall(), koji parsira sve formate.
SQL ORDER BY maknuti (ili ostaviti kao fallback — nije bitno).

Lokacija u app.py: linija 6118-6128 (invoice_list() funkcija)
"""

import shutil, sys, re
from pathlib import Path

APP = Path("app.py")

if not APP.exists():
    print(f"GREŠKA: {APP} nije pronađen!")
    sys.exit(1)

shutil.copy(APP, APP.with_suffix(".py.bak_sort"))
print(f"✅ Backup: app.py.bak_sort")

text = APP.read_text(encoding="utf-8")

# ─── 1. Dodaj helper funkciju (ispred invoice_list route) ────────────────────
HELPER = '''
def _parse_date_sort(s):
    """Parsira datum u usporedivi tuple (god, mj, dan) za sortiranje.
    Podržava: YYYY-MM-DD, DD.MM.YYYY, D.M.YYYY i varijante s točkama."""
    if not s:
        return (0, 0, 0)
    s = str(s).strip().rstrip('.')
    # ISO: YYYY-MM-DD
    m = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})$', s)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    # HR: D.M.YYYY ili DD.MM.YYYY
    m = re.match(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$', s)
    if m:
        return (int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return (0, 0, 0)

'''

ROUTE_MARKER = "@app.route('/invoices')\n@require_perm('can_view_invoices')"

if ROUTE_MARKER in text:
    if '_parse_date_sort' not in text:
        text = text.replace(ROUTE_MARKER, HELPER + ROUTE_MARKER)
        print("✅ _parse_date_sort() helper dodan")
    else:
        print("ℹ️  _parse_date_sort() već postoji")
else:
    print("⚠️  Route marker nije pronađen!")
    sys.exit(1)

# ─── 2. Zamijeni SQL query — makni ORDER BY (Python će sortirati) ─────────────
OLD_QUERY = """    invoices = conn.execute('''
        SELECT i.*, u.username as created_by_username,
               to2.auto_id as pn_auto_id,
               to2.id as pn_order_id
        FROM invoices i
        LEFT JOIN users u ON u.id = i.created_by
        LEFT JOIN pn_expenses pe ON pe.invoice_id = i.id AND pe.travel_order_id IS NOT NULL
        LEFT JOIN travel_orders to2 ON to2.id = pe.travel_order_id
        WHERE i.is_deleted=0 OR i.is_deleted IS NULL
        ORDER BY i.invoice_date DESC, i.id DESC
    ''').fetchall()"""

NEW_QUERY = """    invoices_raw = conn.execute('''
        SELECT i.*, u.username as created_by_username,
               to2.auto_id as pn_auto_id,
               to2.id as pn_order_id
        FROM invoices i
        LEFT JOIN users u ON u.id = i.created_by
        LEFT JOIN pn_expenses pe ON pe.invoice_id = i.id AND pe.travel_order_id IS NOT NULL
        LEFT JOIN travel_orders to2 ON to2.id = pe.travel_order_id
        WHERE i.is_deleted=0 OR i.is_deleted IS NULL
    ''').fetchall()
    # Python sort jer datumi u bazi nisu konzistentno ISO format
    invoices = sorted(
        invoices_raw,
        key=lambda r: (_parse_date_sort(r['invoice_date']), r['id']),
        reverse=True
    )"""

if OLD_QUERY in text:
    text = text.replace(OLD_QUERY, NEW_QUERY)
    print("✅ SQL ORDER BY zamijenjen Python sortom")
else:
    print("⚠️  SQL query nije pronađen točno. Provjeri linije 6118-6128 u app.py.")
    print("    Možda je već patched ili ima whitespace razlike.")
    sys.exit(1)

# ─── 3. Provjeri da import re postoji (potreban za _parse_date_sort) ──────────
if 'import re' not in text:
    text = text.replace('import sqlite3', 'import re\nimport sqlite3')
    print("✅ import re dodan")
else:
    print("ℹ️  import re već postoji")

# ─── Spremi ──────────────────────────────────────────────────────────────────
APP.write_text(text, encoding="utf-8")
print(f"\n✅ app.py snimljen!")

# Provjera
lines = APP.read_text().splitlines()
for i, line in enumerate(lines, 1):
    if '_parse_date_sort' in line or 'Python sort' in line:
        print(f"  L{i}: {line.rstrip()}")

print("\n✅ Gotovo! Restart Flask i testiraj — računi trebaju biti sortirani od najnovijeg.")

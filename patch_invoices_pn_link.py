#!/usr/bin/env python3
"""
Patch: dodaje pn_auto_id i pn_order_id (veza na PN) u /invoices query.

Pokreni PRVI (prije patch_invoice_list.py):
    python3 patch_invoices_pn_link.py
"""
import shutil, os

TARGET = 'app.py'
BACKUP = TARGET + '.bak2'

if not os.path.exists(TARGET):
    print("❌ Nije pronađen app.py"); exit(1)

shutil.copy2(TARGET, BACKUP)
print(f"✅ Backup: {BACKUP}")

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

OLD = """    invoices = conn.execute('''
        SELECT i.*, u.username as created_by_username
        FROM invoices i
        LEFT JOIN users u ON u.id = i.created_by
        WHERE i.is_deleted=0 OR i.is_deleted IS NULL
        ORDER BY i.invoice_date DESC, i.id DESC
    ''').fetchall()"""

NEW = """    invoices = conn.execute('''
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

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    print("✅ FIX: Dodan pn_auto_id + pn_order_id JOIN u /invoices query")
else:
    print("❌ Pattern nije pronađen!"); exit(1)

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print("🎉 app.py patch završen!")

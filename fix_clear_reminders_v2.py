#!/usr/bin/env python3
"""
fix_clear_reminders_v2.py  —  pokreni: python fix_clear_reminders_v2.py
"""
import os, sqlite3

ROOT    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, 'putni_nalog.db')

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Prikaži strukturu tablice
cols = [r[1] for r in conn.execute("PRAGMA table_info(loan_reminders)").fetchall()]
print(f"Kolone u loan_reminders: {cols}\n")

# Prikaži sve zapise
rows = conn.execute("SELECT * FROM loan_reminders ORDER BY rowid DESC").fetchall()
print(f"Zapisi ({len(rows)}):")
for r in rows:
    print(f"  {dict(r)}")

if not rows:
    print("Nema zapisa — ništa za brisati.")
    conn.close()
    exit(0)

print()
print("Briši SVE zapise iz loan_reminders? (da/ne): ", end='')
if input().strip().lower() in ('da', 'd', 'yes', 'y'):
    conn.execute("DELETE FROM loan_reminders")
    conn.commit()
    print(f"✅ Obrisano {len(rows)} zapisa. Sad klikni 'Pokreni provjeru odmah'.")
else:
    print("~ Ništa nije obrisano.")

conn.close()

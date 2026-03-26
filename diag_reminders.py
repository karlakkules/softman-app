#!/usr/bin/env python3
"""
diag_reminders.py  —  pokreni: python3 diag_reminders.py
Dijagnosticira zašto se emaili ne šalju.
"""
import os, sqlite3, json
from datetime import datetime, date, timedelta

ROOT    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, 'putni_nalog.db')

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

today = date.today().isoformat()
print(f"\nDanas: {today}")

# Dohvati postavke
s = {r['key']: r['value'] for r in conn.execute("SELECT key, value FROM settings").fetchall()}
days_before = int(s.get('loan_reminder_days_before') or 0)
target_date = (date.today() + timedelta(days=days_before)).isoformat()
print(f"loan_reminder_days_before: {days_before}")
print(f"Target date (gleda rate za): {target_date}")

# Provjeri kolone u loans
loan_cols = [r[1] for r in conn.execute("PRAGMA table_info(loans)").fetchall()]
print(f"\nKolone u loans: {loan_cols}")
has_emails = 'reminder_emails' in loan_cols
print(f"reminder_emails kolona postoji: {has_emails}")

# Dohvati pozajmice
loans = conn.execute("SELECT * FROM loans").fetchall()
print(f"\nBroj pozajmica: {len(loans)}")

for loan in loans:
    ld = dict(loan)
    emails = ld.get('reminder_emails', '') or ''
    print(f"\n--- Pozajmica: {ld['name']} ---")
    print(f"  reminder_emails: '{emails}'")
    
    # Parsiraj schedule
    schedule = []
    try:
        schedule = json.loads(ld.get('schedule_json') or '[]')
    except:
        pass
    print(f"  Broj rata u rasporedu: {len(schedule)}")
    
    # Pokaži sve neplaćene rate
    unpaid = [e for e in schedule if not e.get('paid')]
    print(f"  Neplaćene rate: {len(unpaid)}")
    for e in unpaid[:5]:
        match = e.get('date') == target_date
        print(f"    Datum: {e.get('date')} | Iznos: {e.get('amount')} | Podudara s target: {'✓' if match else '✗'}")

# Provjeri loan_reminders
lr_cols = [r[1] for r in conn.execute("PRAGMA table_info(loan_reminders)").fetchall()]
print(f"\nKolone u loan_reminders: {lr_cols}")
lr_rows = conn.execute("SELECT * FROM loan_reminders ORDER BY rowid DESC LIMIT 10").fetchall()
print(f"Zapisi u loan_reminders: {len(lr_rows)}")
for r in lr_rows:
    print(f"  {dict(r)}")

conn.close()
print("\n══ Kraj dijagnostike ══\n")

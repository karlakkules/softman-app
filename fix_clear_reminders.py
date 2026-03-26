#!/usr/bin/env python3
"""
fix_clear_reminders.py  —  pokreni: python fix_clear_reminders.py

Briše zapise iz loan_reminders tablice koji su lažno upisani
dok route nije radio ispravno, tako da se emaili mogu ponovo poslati.
"""
import os, sqlite3

ROOT    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, 'putni_nalog.db')

print("\n══════════════════════════════════════════")
print("  Fix: brisanje lažnih loan_reminders")
print("══════════════════════════════════════════\n")

if not os.path.exists(DB_PATH):
    print("❌ Baza nije pronađena!")
    exit(1)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Provjeri postoji li tablica
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
if 'loan_reminders' not in tables:
    print("~ Tablica loan_reminders ne postoji — nema što brisati.")
    conn.close()
    exit(0)

# Prikaži postojeće zapise
rows = conn.execute("""
    SELECT lr.id, lr.loan_id, lr.reminder_date, lr.sent_at, l.name as loan_name
    FROM loan_reminders lr
    LEFT JOIN loans l ON l.id = lr.loan_id
    ORDER BY lr.sent_at DESC
""").fetchall()

if not rows:
    print("~ Nema zapisa u loan_reminders tablici.")
    conn.close()
    exit(0)

print(f"Pronađeni zapisi u loan_reminders ({len(rows)}):\n")
for r in rows:
    print(f"  ID {r['id']} | Pozajmica: {r['loan_name']} | Datum rate: {r['reminder_date']} | Poslano: {r['sent_at']}")

print()
print("Briši sve zapise? (da/ne): ", end='')
odgovor = input().strip().lower()

if odgovor in ('da', 'd', 'yes', 'y'):
    conn.execute("DELETE FROM loan_reminders")
    conn.commit()
    print(f"\n✅ Obrisano {len(rows)} zapisa.")
    print("   Sada možeš kliknuti 'Pokreni provjeru odmah' i emaili će biti poslani.")
else:
    # Nudi brisanje samo za danas
    print()
    print("Briši samo zapise za danas? (da/ne): ", end='')
    samo_danas = input().strip().lower()
    if samo_danas in ('da', 'd', 'yes', 'y'):
        from datetime import date
        today = date.today().isoformat()
        conn.execute("DELETE FROM loan_reminders WHERE sent_at LIKE ?", (today + '%',))
        conn.commit()
        print(f"✅ Obrisani zapisi za danas ({today}).")
    else:
        print("~ Ništa nije obrisano.")

conn.close()
print()
print("Klikni 'Pokreni provjeru odmah' u aplikaciji.")
print("══════════════════════════════════════════\n")

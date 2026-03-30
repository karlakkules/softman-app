#!/usr/bin/env python3
"""
Renumberiranje auto_id za putne naloge 2026-14 do 2026-18.

Plan promjena (po departure_date redoslijedu):
  DB_ID=39  2026-18 → 2026-14  (dep 07.03.)
  DB_ID=33  2026-14 → 2026-15  (dep 11.03.)
  DB_ID=36  2026-15 → 2026-16  (dep 18.03.)
  DB_ID=37  2026-16 → 2026-17  (dep 24.03.)
  DB_ID=38  2026-17 → 2026-18  (dep 24.03.)

Strategija za izbjegavanje UNIQUE konflikta:
  Korak 1: Sve zahvaćene → privremeni prefiks 'TEMP-'
  Korak 2: TEMP- → finalni auto_id

Veze (pn_expenses.travel_order_id) su INTEGER → ne diramo ih.
PDF datoteke se preimeuju ako postoje.

Pokreni: python3 run_pn_renumber.py
"""
import sqlite3, os, shutil

DB = 'putni_nalog.db'
PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdfs')

if not os.path.exists(DB):
    print("❌ Nije pronađen putni_nalog.db"); exit(1)

# ── Definiraj promjene: (db_id, stari_auto_id, novi_auto_id) ───────────────
CHANGES = [
    (39, '2026-18', '2026-14'),
    (33, '2026-14', '2026-15'),
    (36, '2026-15', '2026-16'),
    (37, '2026-16', '2026-17'),
    (38, '2026-17', '2026-18'),
]

# ── Provjera prije izvršavanja ─────────────────────────────────────────────
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")

print("=" * 60)
print("PROVJERA PRIJE IZVRŠAVANJA")
print("=" * 60)
ok = True
for db_id, old_id, new_id in CHANGES:
    row = conn.execute("SELECT id, auto_id, status FROM travel_orders WHERE id=?", (db_id,)).fetchone()
    if not row:
        print(f"❌ DB_ID={db_id} nije pronađen!"); ok = False; continue
    if row['auto_id'] != old_id:
        print(f"❌ DB_ID={db_id} ima auto_id='{row['auto_id']}', očekivano '{old_id}'")
        ok = False; continue
    print(f"  ✅ DB_ID={db_id:3d}  {old_id:12s} → {new_id:12s}  status={row['status']}")

if not ok:
    print("\n❌ Provjera nije prošla — ništa nije promijenjeno!")
    conn.close(); exit(1)

print()
print("Nastavljam s renumberiranjem...")
print()

# ── Izvršavanje u jednoj transakciji ──────────────────────────────────────
try:
    conn.execute("BEGIN")

    # Korak 1: Sve zahvaćene → privremeni TEMP- prefiks
    for db_id, old_id, new_id in CHANGES:
        temp_id = f"TEMP-{old_id}"
        conn.execute("UPDATE travel_orders SET auto_id=? WHERE id=?", (temp_id, db_id))
        print(f"  [1] DB_ID={db_id}  {old_id} → {temp_id}")

    # Korak 2: TEMP- → finalni auto_id
    for db_id, old_id, new_id in CHANGES:
        temp_id = f"TEMP-{old_id}"
        conn.execute("UPDATE travel_orders SET auto_id=?, updated_at=datetime('now') WHERE id=?",
                     (new_id, db_id))
        print(f"  [2] DB_ID={db_id}  {temp_id} → {new_id}")

    # Korak 3: Ažuriraj settings.last_order_number na max aktivni broj
    max_num = max(int(new_id.split('-')[1]) for _, _, new_id in CHANGES)
    # Provjeri postoji li veći broj od aktivnih naloga
    all_active = conn.execute(
        "SELECT auto_id FROM travel_orders WHERE auto_id LIKE '2026-%' AND auto_id NOT LIKE '%-I' AND (is_deleted=0 OR is_deleted IS NULL)"
    ).fetchall()
    actual_max = max(int(r['auto_id'].split('-')[1]) for r in all_active if r['auto_id'].count('-') == 1)
    conn.execute("UPDATE settings SET value=? WHERE key='last_order_number'", (str(actual_max),))
    print(f"  [3] settings.last_order_number → {actual_max}")

    conn.execute("COMMIT")
    print()
    print("✅ Baza uspješno ažurirana!")

except Exception as e:
    conn.execute("ROLLBACK")
    print(f"\n❌ GREŠKA — rollback izvršen: {e}")
    conn.close(); exit(1)

# ── Korak 4: Preimenuj PDF datoteke ako postoje ───────────────────────────
print()
print("Pregled PDF datoteka...")
pdf_renames = 0
pdf_missing = 0

for db_id, old_id, new_id in CHANGES:
    old_pdf = os.path.join(PDF_DIR, f"PN_{old_id}.pdf")
    new_pdf = os.path.join(PDF_DIR, f"PN_{new_id}.pdf")
    if os.path.exists(old_pdf):
        # Provjeri da novi naziv već ne postoji
        if os.path.exists(new_pdf):
            print(f"  ⚠️  {new_pdf} već postoji — preskaćem rename")
        else:
            shutil.move(old_pdf, new_pdf)
            print(f"  📄 PDF: PN_{old_id}.pdf → PN_{new_id}.pdf")
            pdf_renames += 1
        # Ažuriraj pdf_path u bazi
        conn.execute("UPDATE travel_orders SET pdf_path=? WHERE id=?",
                     (f"PN_{new_id}.pdf", db_id))
        conn.commit()
    else:
        print(f"  —  Nema PDF za PN_{old_id} (nije odobreno ili nije generirano)")
        pdf_missing += 1

# ── Završna provjera ───────────────────────────────────────────────────────
print()
print("=" * 60)
print("ZAVRŠNO STANJE")
print("=" * 60)
final = conn.execute("""
    SELECT to2.id, to2.auto_id, to2.departure_date, to2.status, e.name
    FROM travel_orders to2
    LEFT JOIN employees e ON e.id = to2.employee_id
    WHERE to2.auto_id LIKE '2026-1%' OR to2.auto_id LIKE '2026-2%'
    ORDER BY CAST(SUBSTR(to2.auto_id, 6) AS INTEGER) ASC
""").fetchall()

for r in final:
    print(f"  DB_ID={r['id']:3d}  {r['auto_id']:12s}  dep={r['departure_date'] or '':12s}  "
          f"status={r['status']:10s}  {r[4] or ''}")

print()
print(f"✅ Gotovo! PDF renames: {pdf_renames}, bez PDF-a: {pdf_missing}")
print()
print("VEZE su sigurne — pn_expenses koristi travel_order_id (INTEGER), nije promijenjen.")

conn.close()

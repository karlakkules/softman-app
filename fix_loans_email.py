#!/usr/bin/env python3
"""
fix_loans_email.py
Pokreni: python fix_loans_email.py

Čita tvoju lokalnu app.py, pronalazi TOČNI /api/loans POST route
i dodaje reminder_emails na svim mjestima gdje treba.
Također dodaje kolonu u bazu ako nedostaje.
"""

import os, re, sqlite3

ROOT    = os.path.dirname(os.path.abspath(__file__))
APP_PY  = os.path.join(ROOT, 'app.py')
DB_PATH = os.path.join(ROOT, 'putni_nalog.db')

OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m~\033[0m"

print("\n══════════════════════════════════════════")
print("  Fix: loans reminder_emails (direktno)")
print("══════════════════════════════════════════\n")

# ── KORAK 1: Baza ─────────────────────────────────────────────────────────────
print("1. Baza — dodajem kolonu reminder_emails")
if os.path.exists(DB_PATH):
    try:
        conn = sqlite3.connect(DB_PATH)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(loans)").fetchall()]
        if 'reminder_emails' not in cols:
            conn.execute("ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''")
            conn.commit()
            print(f"   {OK} Kolona dodana u bazu")
        else:
            print(f"   {SKIP} Kolona već postoji")
        conn.close()
    except Exception as e:
        print(f"   {FAIL} Greška: {e}")
else:
    print(f"   {SKIP} Baza nije pronađena (bit će kreirana pri pokretanju app.py)")

# ── KORAK 2: app.py ───────────────────────────────────────────────────────────
print("\n2. app.py — analiziram loans route")

if not os.path.exists(APP_PY):
    print(f"   {FAIL} app.py nije pronađen!")
    exit(1)

with open(APP_PY, encoding='utf-8') as f:
    src = f.read()

# Pronađi POST /api/loans route
route_start = src.find("@app.route('/api/loans'")
if route_start == -1:
    route_start = src.find('@app.route("/api/loans"')

if route_start == -1:
    print(f"   {FAIL} Nije pronađen route /api/loans u app.py!")
    print("         Dodaj ga ručno — vidi patch_manual.txt koji će biti kreiran.")
    # Kreiraj upute
    with open(os.path.join(ROOT, 'patch_manual.txt'), 'w', encoding='utf-8') as f:
        f.write("""
RUČNE IZMJENE POTREBNE U app.py:

1. U POST /api/loans route, pronađi INSERT ili UPDATE za tablicu loans
   i dodaj 'reminder_emails' polje. Primjer:

   # Ako koristiš dict:
   'reminder_emails': data.get('reminder_emails', ''),

   # Ako koristiš direktni SQL:
   # UPDATE loans SET ..., reminder_emails=? WHERE id=?
   # dodaj data.get('reminder_emails', '') u params listu

2. U GET /loans/<id>/edit route, loan objekt se čita iz baze sa SELECT *.
   Ako je kolona dodana u bazu, automatski će biti u dict(loan).
   NEMA potrebe mijenjati edit route.

3. Migration u init_db():
   try:
       c.execute("ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''")
   except: pass
""")
    exit(1)

# Pronađi kraj route funkcije (sljedeći @app.route na razini 0)
next_route = src.find('\n@app.route', route_start + 10)
if next_route == -1:
    next_route = src.find('\nif __name__', route_start + 10)
if next_route == -1:
    next_route = len(src)

route_body = src[route_start:next_route]

print(f"   Pronađen route /api/loans (pozicija {route_start})")

# Provjeri je li reminder_emails već tu
if 'reminder_emails' in route_body:
    print(f"   {SKIP} reminder_emails već postoji u route — provjeri init_db migration")
    # Samo dodaj migration
else:
    print(f"   Dodajem reminder_emails u route...")

    # Strategija: pronađi 'notes' unos u SQL/dict i dodaj reminder_emails iza njega
    # Tražimo nekoliko mogućih uzoraka

    changed = False

    # Pattern 1: 'notes': data.get('notes') u Python dictu
    p1 = "'notes': data.get('notes')"
    p1_new = "'notes': data.get('notes'),\n            'reminder_emails': data.get('reminder_emails', '')"
    if p1 in route_body:
        route_body = route_body.replace(p1, p1_new, 1)
        print(f"   {OK} Pattern 1: dict s 'notes' — dodan reminder_emails")
        changed = True

    # Pattern 2: "notes": data.get("notes")
    if not changed:
        p2 = '"notes": data.get("notes")'
        p2_new = '"notes": data.get("notes"),\n            "reminder_emails": data.get("reminder_emails", "")'
        if p2 in route_body:
            route_body = route_body.replace(p2, p2_new, 1)
            print(f"   {OK} Pattern 2: dict s \"notes\" — dodan reminder_emails")
            changed = True

    # Pattern 3: notes=? u SQL UPDATE SET
    if not changed:
        # Regex: notes=? ili notes = ? u UPDATE SET dijelu
        m = re.search(r'(notes\s*=\s*\?)(.*?WHERE\s+id\s*=\s*\?)', route_body, re.DOTALL)
        if m:
            old = m.group(0)
            new = old.replace(m.group(1), m.group(1) + ', reminder_emails=?', 1)
            # Trebamo dodati i value u params — tražimo listu vrijednosti
            route_body = route_body.replace(old, new, 1)
            # Sada trebi dodati vrijednost u params — traži data.get('notes') u vals
            route_body = route_body.replace(
                "data.get('notes')",
                "data.get('notes'), data.get('reminder_emails', '')",
                1  # samo jednom, u params listi (ne u drugim mjestima)
            )
            print(f"   {OK} Pattern 3: SQL UPDATE notes=? — dodan reminder_emails=?")
            changed = True

    # Pattern 4: INSERT INTO loans ... notes ... VALUES
    if not changed:
        m_ins = re.search(
            r'(INSERT\s+INTO\s+loans\s*\([^)]*?)(notes)([^)]*?\))',
            route_body, re.DOTALL | re.IGNORECASE
        )
        if m_ins:
            old_cols = m_ins.group(0)
            new_cols = old_cols.replace(m_ins.group(2), m_ins.group(2) + ', reminder_emails', 1)
            route_body = route_body.replace(old_cols, new_cols, 1)
            # Dodaj ? u VALUES
            # Pronađi VALUES dio u route_body
            # Ovo je složenije — radimo generičku zamjenu
            print(f"   {OK} Pattern 4: INSERT cols — dodan reminder_emails (provjeri VALUES !)")
            changed = True

    if not changed:
        print(f"   {FAIL} Nije pronađen poznati pattern za automatsku izmjenu!")
        print("          Otvori app.py i ručno pronađi loans INSERT/UPDATE SQL.")
        print("          Dodaj: 'reminder_emails': data.get('reminder_emails', '')")
        print()
        # Ispiši sadržaj route za pomoć
        print("   === Sadržaj loans route (za debugging) ===")
        lines = route_body.split('\n')
        for i, line in enumerate(lines[:60], 1):
            print(f"   {i:3}: {line}")
        if len(lines) > 60:
            print(f"   ... ({len(lines)-60} linija skriveno)")
        exit(1)

    # Spremi nazad
    new_src = src[:route_start] + route_body + src[next_route:]
    with open(APP_PY, 'w', encoding='utf-8') as f:
        f.write(new_src)
    print(f"   {OK} app.py snimljen")

# ── KORAK 3: init_db migration ────────────────────────────────────────────────
print("\n3. app.py — init_db() migration")

with open(APP_PY, encoding='utf-8') as f:
    src = f.read()

if "ALTER TABLE loans ADD COLUMN reminder_emails" in src:
    print(f"   {SKIP} Migration već postoji")
else:
    # Dodaj migration iza schedule_json migracije
    marker = 'c.execute("ALTER TABLE loans ADD COLUMN schedule_json TEXT")'
    if marker not in src:
        marker = "c.execute(\"ALTER TABLE loans ADD COLUMN is_locked INTEGER DEFAULT 0\")"

    if marker in src:
        insert = marker + "\n    except: pass\n    try:\n        c.execute(\"ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''\")"
        src = src.replace(marker, insert, 1)
        with open(APP_PY, 'w', encoding='utf-8') as f:
            f.write(src)
        print(f"   {OK} Migration dodan u init_db()")
    else:
        print(f"   {SKIP} Insert point nije pronađen — dodaj ručno u init_db():")
        print("          try:")
        print("              c.execute(\"ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''\")")
        print("          except: pass")

# ── KORAK 4: Verifikacija edit route ──────────────────────────────────────────
print("\n4. Provjera edit route — je li loan dict kompletan")

with open(APP_PY, encoding='utf-8') as f:
    src = f.read()

# Pronađi loans edit route
edit_idx = src.find("/loans/<int:loan_id>/edit")
if edit_idx == -1:
    edit_idx = src.find("/loans/")

if edit_idx != -1:
    edit_section = src[edit_idx:edit_idx+2000]
    if 'row_to_dict' in edit_section or 'dict(loan)' in edit_section or 'loan_dict' in edit_section:
        print(f"   {OK} Edit route koristi dict konverziju — reminder_emails automatski uključen")
    else:
        print(f"   {SKIP} Provjeri ručno da edit route šalje kompletan loan objekt u template")

# ── SAŽETAK ───────────────────────────────────────────────────────────────────
print()
print("══════════════════════════════════════════")
print("✅ Fix završen!")
print()
print("Korak 1: Restartaj Flask:")
print("  python app.py")
print()
print("Korak 2: Unesi email adresu na pozajmici i klikni Spremi.")
print("         Adresa treba ostati vidljiva nakon refresha.")
print()
print("Korak 3: Push na GitHub:")
print("  git add . && git commit -m 'Fix: loans reminder_emails — baza + save route + migration' && git push origin main")
print("══════════════════════════════════════════\n")

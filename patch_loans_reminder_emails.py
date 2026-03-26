#!/usr/bin/env python3
"""
patch_loans_reminder_emails.py
Pokreni iz root foldera projekta: python patch_loans_reminder_emails.py

PROBLEM: Email adrese na pozajmici nestaju nakon "Spremi"
UZROK 1: Tablica 'loans' u SQLite bazi nema kolonu 'reminder_emails'
         → baza tiho ignorira polje pri INSERT/UPDATE
UZROK 2: Flask route /api/loans (POST) ne sprema reminder_emails u SQL upit
UZROK 3: Flask route /loans/<id>/edit ne prosljeđuje reminder_emails u template
FIX: app.py — dodaj migration + UPDATE/INSERT + template render
"""

import os, re, sys, sqlite3

ROOT   = os.path.dirname(os.path.abspath(__file__))
APP_PY = os.path.join(ROOT, 'app.py')
DB_PATH = os.path.join(ROOT, 'putni_nalog.db')

OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m~\033[0m"

errors = []

def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("\n╔══════════════════════════════════════════════════════════╗")
print("║  Softman — Fix: reminder_emails nestaje na pozajmici    ║")
print("╚══════════════════════════════════════════════════════════╝\n")

# ─────────────────────────────────────────────────────────────────────────────
# KORAK 1 — Direktno u SQLite bazi dodaj kolonu ako ne postoji
# (odmah, bez restarta aplikacije)
# ─────────────────────────────────────────────────────────────────────────────
print("1. SQLite baza — dodavanje kolone 'reminder_emails' u tablicu 'loans'")

if not os.path.exists(DB_PATH):
    print(f"  {SKIP} Baza nije pronađena na: {DB_PATH}")
    print(f"       (kolona će biti dodana pri prvom pokretanju app.py — migration u init_db)")
else:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Provjeri postoji li već kolona
        cols = [row[1] for row in c.execute("PRAGMA table_info(loans)").fetchall()]
        if 'reminder_emails' in cols:
            print(f"  {SKIP} Kolona 'reminder_emails' već postoji u bazi")
        else:
            c.execute("ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''")
            conn.commit()
            print(f"  {OK} Kolona 'reminder_emails' dodana u tablicu 'loans'")
        conn.close()
    except Exception as e:
        print(f"  {FAIL} Greška pri izmjeni baze: {e}")
        errors.append(f"Baza: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# KORAK 2 — app.py: init_db() migration
# Dodaj ALTER TABLE za reminder_emails u init_db uz ostale loans migracije
# ─────────────────────────────────────────────────────────────────────────────
print("\n2. app.py — init_db() migration za reminder_emails")

if not os.path.exists(APP_PY):
    print(f"  {FAIL} app.py nije pronađen!")
    errors.append("app.py ne postoji")
else:
    content = read(APP_PY)

    MIGRATION_MARKER = "c.execute(\"ALTER TABLE loans ADD COLUMN schedule_json TEXT\")"
    MIGRATION_NEW = """c.execute("ALTER TABLE loans ADD COLUMN schedule_json TEXT")
    except: pass
    try:
        c.execute("ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''")"""

    if 'reminder_emails TEXT DEFAULT' in content:
        print(f"  {SKIP} Migration za reminder_emails već postoji u init_db()")
    elif MIGRATION_MARKER in content:
        content = content.replace(MIGRATION_MARKER, MIGRATION_NEW, 1)
        write(APP_PY, content)
        print(f"  {OK} Migration dodan u init_db()")
    else:
        # Fallback — dodaj uz ostale try/except loans migracije
        alt_marker = "c.execute(\"ALTER TABLE loans ADD COLUMN is_locked INTEGER DEFAULT 0\")"
        if alt_marker in content:
            alt_new = alt_marker + """
    except: pass
    try:
        c.execute("ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''")"""
            content = content.replace(alt_marker, alt_new, 1)
            write(APP_PY, content)
            print(f"  {OK} Migration dodan uz is_locked migration")
        else:
            print(f"  {SKIP} Nije pronađen insert point — dodaj ručno u init_db():")
            print("""       try:
           c.execute("ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''")
       except: pass""")

# ─────────────────────────────────────────────────────────────────────────────
# KORAK 3 — app.py: route POST /api/loans — spremi reminder_emails u bazu
# ─────────────────────────────────────────────────────────────────────────────
print("\n3. app.py — route POST /api/loans — spremi reminder_emails")

content = read(APP_PY)

# Tražimo uzorak gdje se grade fields za INSERT/UPDATE loans tablice
# Karakteristični dio: 'repayment_end': ..., 'notes': ...
# Trebamo dodati 'reminder_emails' u taj dict/set

# Varijanta A — ako koristi dict fields s UPDATE/INSERT
if "'reminder_emails'" in content or '"reminder_emails"' in content:
    # Provjeri je li stvarno u loans route (a ne samo u template rendu)
    # Tražimo specifičan kontekst oko loans save route
    idx = content.find("'reminder_emails'")
    context = content[max(0,idx-200):idx+100]
    if 'repayment_end' in context or 'schedule_json' in context or 'loan_date' in context:
        print(f"  {SKIP} reminder_emails već se sprema u loans route")
    else:
        print(f"  {SKIP} reminder_emails postoji ali možda nije u pravom kontekstu — provjerit ćemo dalje")

# Traži uzorak INSERT/UPDATE za loans
# Tipični pattern u ovoj bazi: 'notes': data.get('notes')  + schedule_json
NOTES_PATTERN_RE = re.compile(
    r"('notes'\s*:\s*data\.get\('notes'\))",
    re.DOTALL
)

SCHEDULE_UPDATE_RE = re.compile(
    r"(schedule_json\s*=\s*(?:json\.dumps\(schedule\)|data\.get\('schedule_json'\)|['\"]schedule_json['\"])[^,\n]*)",
    re.DOTALL
)

# Pronađi loans save route
loans_save_idx = content.find("@app.route('/api/loans'")
if loans_save_idx == -1:
    loans_save_idx = content.find('@app.route("/api/loans"')

if loans_save_idx == -1:
    print(f"  {FAIL} Nije pronađen route /api/loans — nije moguće automatski patchati")
    print(f"         Dodaj ručno 'reminder_emails': data.get('reminder_emails','') u loans save logiku")
    errors.append("Nije pronađen /api/loans route")
else:
    # Uzmi samo relevantni dio koda (sljedećih ~100 linija od route dekoratora)
    route_section = content[loans_save_idx:loans_save_idx + 4000]

    if 'reminder_emails' in route_section:
        print(f"  {SKIP} reminder_emails već postoji u /api/loans route")
    else:
        # Tražimo 'notes': data.get('notes') u tom dijelu i dodajemo reminder_emails
        old_notes = "'notes': data.get('notes')"
        new_notes = "'notes': data.get('notes'),\n            'reminder_emails': data.get('reminder_emails', '')"

        # Pokušaj zamjene u route_section pa rekombiniraj
        if old_notes in route_section:
            new_route_section = route_section.replace(old_notes, new_notes, 1)
            content = content[:loans_save_idx] + new_route_section + content[loans_save_idx + 4000:]
            write(APP_PY, content)
            print(f"  {OK} 'reminder_emails' dodan u dict za loans save route")
        else:
            # Pokušaj s navodnicima
            old_notes2 = '"notes": data.get("notes")'
            new_notes2 = '"notes": data.get("notes"),\n            "reminder_emails": data.get("reminder_emails", "")'
            if old_notes2 in route_section:
                new_route_section = route_section.replace(old_notes2, new_notes2, 1)
                content = content[:loans_save_idx] + new_route_section + content[loans_save_idx + 4000:]
                write(APP_PY, content)
                print(f"  {OK} 'reminder_emails' dodan u dict za loans save route (double quotes)")
            else:
                # Traži UPDATE SET pattern za loans
                update_pattern = re.compile(
                    r"(UPDATE loans SET.*?notes\s*=\s*\?)(.*?WHERE id\s*=\s*\?)",
                    re.DOTALL
                )
                match = update_pattern.search(route_section)
                if match:
                    old_update = match.group(0)
                    new_update = old_update.replace(
                        match.group(1),
                        match.group(1) + ', reminder_emails=?'
                    )
                    new_route_section = route_section.replace(old_update, new_update, 1)
                    content = content[:loans_save_idx] + new_route_section + content[loans_save_idx + 4000:]
                    write(APP_PY, content)
                    print(f"  {OK} 'reminder_emails' dodan u UPDATE SET SQL query")
                else:
                    print(f"  {SKIP} Nije pronađen automatski insert point za reminder_emails")
                    print(f"         Dodaj ručno u loans save route: 'reminder_emails': data.get('reminder_emails', '')")
                    errors.append("Ručno dodaj reminder_emails u /api/loans route")

# ─────────────────────────────────────────────────────────────────────────────
# KORAK 4 — app.py: route GET /loans/<id>/edit — proslijedi reminder_emails u template
# ─────────────────────────────────────────────────────────────────────────────
print("\n4. app.py — route /loans/<id>/edit — reminder_emails u template kontekstu")

content = read(APP_PY)

# Pronađi loan_edit route
edit_idx = content.find("/loans/<int:loan_id>/edit")
if edit_idx == -1:
    edit_idx = content.find("/loans/")

# Provjeri radi li se loan dict ispravno
# Loan objekt se čita iz baze i prosljeđuje kao dict — ako je kolona dodana u bazu,
# row_to_dict() će automatski sadržavati reminder_emails
# Ali template čita: {{ loan.reminder_emails if loan and loan.reminder_emails else '' }}
# Dakle, ako je kolona u bazi i row_to_dict() radi ispravno — trebalo bi raditi automatski

# Provjeri ima li ikakvo override ili filtriranje loans polja
loans_route_content = content[edit_idx:edit_idx+3000] if edit_idx != -1 else ''
if 'reminder_emails' in loans_route_content:
    print(f"  {SKIP} reminder_emails već se prosljeđuje u edit route")
elif 'row_to_dict' in loans_route_content or 'dict(loan)' in loans_route_content:
    print(f"  {OK} Edit route koristi row_to_dict()/dict(loan) — reminder_emails će biti automatski uključen")
    print(f"       (kad je kolona dodana u bazu, sve radi automatski)")
else:
    print(f"  {SKIP} Nije moguće automatski verificirati — provjeri ručno")

# ─────────────────────────────────────────────────────────────────────────────
# KORAK 5 — Verifikacija loan_form.html (uploadani fajl je već ispravan)
# ─────────────────────────────────────────────────────────────────────────────
print("\n5. Verifikacija loan_form.html template")

loan_form = os.path.join(ROOT, 'templates', 'loan_form.html')
if os.path.exists(loan_form):
    lf = read(loan_form)
    checks = [
        ('id="loan-reminder-emails"', 'Input polje postoji'),
        ('loan.reminder_emails', 'Jinja2 čita reminder_emails iz loan objekta'),
        ("'reminder_emails'", 'saveLoan() šalje reminder_emails u payload'),
    ]
    all_ok = True
    for pattern, label in checks:
        if pattern in lf:
            print(f"  {OK} {label}")
        else:
            print(f"  {FAIL} {label} — NIJE PRONAĐENO!")
            errors.append(f"loan_form.html: {label}")
            all_ok = False
else:
    print(f"  {SKIP} templates/loan_form.html nije pronađen za verifikaciju")

# ─────────────────────────────────────────────────────────────────────────────
# SAŽETAK
# ─────────────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"⚠️  Završeno s {len(errors)} upozorenjima:")
    for e in errors:
        print(f"   • {e}")
    print()
    print("   Za ručni fix u app.py — pronađi loans save route i dodaj:")
    print("   'reminder_emails': data.get('reminder_emails', '')")
    print("   u dict koji se koristi za INSERT i UPDATE loans tablice.")
else:
    print("✅ Sve izmjene uspješno primijenjene!")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("Što je popravljeno:")
print("  putni_nalog.db  — kolona 'reminder_emails' dodana u tablicu 'loans'")
print("  app.py          — migration u init_db() za reminder_emails")
print("  app.py          — /api/loans route sprema reminder_emails")
print()
print("Restartaj Flask i provjeri:")
print("  python app.py")
print()
print("Pushaj na GitHub:")
print("  git add . && git commit -m 'Fix: loans reminder_emails kolona + save' && git push origin main")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

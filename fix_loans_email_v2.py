#!/usr/bin/env python3
"""
fix_loans_email_v2.py  —  pokreni: python fix_loans_email_v2.py
"""
import os, sqlite3

ROOT    = os.path.dirname(os.path.abspath(__file__))
APP_PY  = os.path.join(ROOT, 'app.py')
DB_PATH = os.path.join(ROOT, 'putni_nalog.db')

OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m~\033[0m"

print("\n══════════════════════════════════════════")
print("  Fix v2: loans reminder_emails")
print("══════════════════════════════════════════\n")

# ── 1. Baza ────────────────────────────────────────────────────────────────────
print("1. Baza")
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(loans)").fetchall()]
    if 'reminder_emails' not in cols:
        conn.execute("ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''")
        conn.commit()
        print(f"   {OK} Kolona dodana")
    else:
        print(f"   {SKIP} Kolona već postoji")
    conn.close()
else:
    print(f"   {SKIP} Baza nije pronađena")

# ── 2. app.py — fields dict ────────────────────────────────────────────────────
print("\n2. app.py — dodajem reminder_emails u fields dict")

with open(APP_PY, encoding='utf-8') as f:
    src = f.read()

OLD = "        'notes': data.get('notes',''),\n        'updated_at': datetime.now().isoformat(),"
NEW = "        'notes': data.get('notes',''),\n        'reminder_emails': data.get('reminder_emails', ''),\n        'updated_at': datetime.now().isoformat(),"

if 'reminder_emails' in src[src.find("@app.route('/api/loans'"):src.find("@app.route('/api/loans'")+2000]:
    print(f"   {SKIP} reminder_emails već postoji u route")
elif OLD in src:
    src = src.replace(OLD, NEW, 1)
    with open(APP_PY, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f"   {OK} Dodano u fields dict")
else:
    print(f"   {FAIL} Pattern nije pronađen — dodaj ručno u app.py:")
    print("          Pronađi liniju:  'notes': data.get('notes',''),")
    print("          Dodaj ispod:     'reminder_emails': data.get('reminder_emails', ''),")

# ── 3. init_db migration ───────────────────────────────────────────────────────
print("\n3. init_db() migration")

with open(APP_PY, encoding='utf-8') as f:
    src = f.read()

if "ALTER TABLE loans ADD COLUMN reminder_emails" in src:
    print(f"   {SKIP} Migration već postoji")
else:
    marker = 'c.execute("ALTER TABLE loans ADD COLUMN schedule_json TEXT")'
    if marker in src:
        src = src.replace(
            marker,
            marker + "\n    except: pass\n    try:\n        c.execute(\"ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''\")",
            1
        )
        with open(APP_PY, 'w', encoding='utf-8') as f:
            f.write(src)
        print(f"   {OK} Migration dodan")
    else:
        print(f"   {SKIP} Dodaj ručno u init_db() blok migrations za loans:")
        print("          try:")
        print("              c.execute(\"ALTER TABLE loans ADD COLUMN reminder_emails TEXT DEFAULT ''\")")
        print("          except: pass")

print()
print("✅ Gotovo! Pokreni:")
print("   python app.py")
print()
print("Push:")
print("   git add . && git commit -m 'Fix: loans reminder_emails' && git push origin main")
print("══════════════════════════════════════════\n")

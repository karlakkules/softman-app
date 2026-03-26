#!/usr/bin/env python3
"""
patch_softman.py
Pokreni iz root foldera projekta: python patch_softman.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(ROOT, "templates")

OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m~\033[0m"

errors = []

def patch_file(filename, description, find, replace):
    path = os.path.join(TEMPLATES, filename)
    if not os.path.exists(path):
        print(f"  {FAIL} {filename} — FAJL NIJE PRONAĐEN")
        errors.append(f"{filename}: fajl ne postoji")
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if find not in content:
        print(f"  {SKIP} {filename} — '{description}' već primijenjeno ili tekst nije pronađen")
        return

    new_content = content.replace(find, replace, 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"  {OK} {filename} — {description}")


print("\n╔══════════════════════════════════════════╗")
print("║       Softman App — Patch Script         ║")
print("╚══════════════════════════════════════════╝\n")

# ─────────────────────────────────────────────────────────────────
# IZMJENA 1: orders.html — "Brzi unos troška" → "Unos troška"
# Mijenjamo sve varijante teksta (data-hr, data-en, title, vidljivi tekst)
# ─────────────────────────────────────────────────────────────────
print("1. orders.html — preimenovanje gumba 'Brzi unos troška'")

# Pokušaj A — ako postoji točan span s data-hr
patch_file(
    "orders.html",
    "Rename: Brzi unos troška → Unos troška (span data-hr)",
    'data-hr="Brzi unos troška"',
    'data-hr="Unos troška"'
)

patch_file(
    "orders.html",
    "Rename: Quick Expense → Add Expense (data-en)",
    'data-en="Quick Expense"',
    'data-en="Add Expense"'
)

# Vidljivi tekst unutar spana
patch_file(
    "orders.html",
    "Rename: vidljivi tekst Brzi unos troška",
    '>Brzi unos troška</span>',
    '>Unos troška</span>'
)

# title atribut gumba
patch_file(
    "orders.html",
    "Rename: title Brzi unos troška",
    'title="Brzi unos troška"',
    'title="Unos troška"'
)


# ─────────────────────────────────────────────────────────────────
# IZMJENA 2: form.html — PDF ikona u sekciji "Troškovi s dokumentima"
# Zamjena emoji/stare ikone s crvenim PDF SVG-om
# ─────────────────────────────────────────────────────────────────
print("\n2. form.html — zamjena ikone za otvaranje PDF dokumenta troška")

PDF_SVG = (
    '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M3 1h7l3 3v10a1 1 0 01-1 1H3a1 1 0 01-1-1V2a1 1 0 011-1z" fill="#e74c3c" stroke="#c0392b" stroke-width="0.5"/>'
    '<path d="M10 1l3 3h-3V1z" fill="#c0392b"/>'
    '<text x="3.5" y="11.5" font-family="Arial" font-size="4.5" font-weight="bold" fill="white">PDF</text>'
    '</svg>'
)

# Varijanta A — emoji 📄
patch_file(
    "form.html",
    "Zamjena ikone 📄 s PDF SVG-om (troškovi s dokumentima)",
    '📄',
    PDF_SVG
)

# Varijanta B — tekst ikone "pdf" ili stara SVG s file ikonom
# Pokušavamo pronaći pattern s klasom btn u sekciji troškova s dokumentima
orders_form_path = os.path.join(TEMPLATES, "form.html")
if os.path.exists(orders_form_path):
    with open(orders_form_path, "r", encoding="utf-8") as f:
        fc = f.read()

    # Traži gumb koji otvara file dokumenta troška — ima href s /file i nema crveni PDF SVG
    # Pattern: <a href="...expenses.../file..." target="_blank" ... >  NEŠTO  </a>
    # gdje NEŠTO nije crveni PDF SVG
    pattern = re.compile(
        r'(<a\s[^>]*?/expenses/[^>]*?/file[^>]*?>[^<]*?)(📄|'
        r'<svg[^>]*?>.*?</svg>)(.*?</a>)',
        re.DOTALL
    )

    already_has_red_pdf = '#e74c3c' in fc
    if already_has_red_pdf:
        print(f"  {SKIP} form.html — crveni PDF SVG već postoji u troškovima")
    else:
        new_fc, n = re.subn(
            r'(<a\b[^>]*?(?:expenses|doc)[^>]*?/file[^>]*?>)\s*(📄|[\U0001F4C4])\s*(</a>)',
            lambda m: m.group(1) + '\n    ' + PDF_SVG + '\n  ' + m.group(3),
            fc, flags=re.DOTALL
        )
        if n:
            with open(orders_form_path, "w", encoding="utf-8") as f:
                f.write(new_fc)
            print(f"  {OK} form.html — zamjena emoji ikone regex ({n} pojavljivanja)")
        else:
            print(f"  {SKIP} form.html — nije pronađen poznati pattern za emoji ikonu (regex)")


# ─────────────────────────────────────────────────────────────────
# SAŽETAK
# ─────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"⚠️  Završeno s {len(errors)} greškom/ama:")
    for e in errors:
        print(f"   • {e}")
else:
    print("✅ Sve izmjene uspješno primijenjene!")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("Sljedeći korak — pokreni Flask i provjeri:")
print("  python app.py")
print()
print("Kada si zadovoljan, pushaj na GitHub:")
print("  git add . && git commit -m 'UI: Unos troška rename + crveni PDF SVG u troškovima PN' && git push origin main")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

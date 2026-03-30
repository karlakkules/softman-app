#!/usr/bin/env python3
"""
Patch: app.py
calculate_dnevnice() — ispravka granice za punu dnevnicu:
  < 8h  → 0 (nema dnevnice)
  8-11h → 0.5 (pola dnevnice)  
  ≥ 12h → 1.0 (puna dnevnica)

Prethodno: remaining_hours <= 12 davao je 0.5 za točno 12h — pogrešno.
Ispravno:  remaining_hours >= 12 daje 1.0 (točno 12h = puna dnevnica).
"""
import shutil, os, sys

APP = os.path.join(os.path.dirname(__file__), 'app.py')

if not os.path.exists(APP):
    print(f"❌ Nije pronađen: {APP}")
    sys.exit(1)

shutil.copy(APP, APP + '.bak3')
print("✅ Backup kreiran: app.py.bak3")

with open(APP, 'r', encoding='utf-8') as f:
    src = f.read()

OLD = """        # Calculate dnevnice
        dnevnice = total_days  # full days
        if remaining_hours < 8:
            pass  # no extra dnevnica
        elif remaining_hours <= 12:
            dnevnice += 0.5
        else:
            dnevnice += 1.0"""

NEW = """        # Calculate dnevnice (prema HR pravilima)
        # < 8h  → nema extra dnevnice
        # 8–11h → pola dnevnice (0.5)
        # ≥ 12h → puna dnevnica (1.0)
        dnevnice = total_days  # full days
        if remaining_hours < 8:
            pass  # nema extra dnevnice
        elif remaining_hours < 12:
            dnevnice += 0.5
        else:
            dnevnice += 1.0"""

if OLD not in src:
    print("❌ PATCH PRESKOČEN — pattern nije pronađen")
    print(f"   Tražim: {repr(OLD[:80])}")
    sys.exit(1)

src = src.replace(OLD, NEW, 1)
print("✅ Patch primijenjen: calculate_dnevnice() granica 12h = puna dnevnica")

with open(APP, 'w', encoding='utf-8') as f:
    f.write(src)

print("\n🎉 app.py uspješno ažuriran!")
print("   Provjera: 1d 12h 10min → 2 dnevnice (1 za dan + 1 za ≥12h ostatak)")
print("   Provjera: 1d 11h 59min → 1.5 dnevnice (1 za dan + 0.5 za 8-11h)")
print("   Provjera: 1d 7h 59min  → 1 dnevnica (samo puni dan, < 8h ostatak)")

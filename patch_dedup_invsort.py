#!/usr/bin/env python3
"""
Ukloni dupli invSort JS blok iz invoice_list.html.
Problem: invSort() i DOMContentLoaded postoje 2x — drugi poziv invertira sort.
"""
import shutil, sys, re
from pathlib import Path

TEMPLATE = Path("templates/invoice_list.html")
if not TEMPLATE.exists():
    print(f"GREŠKA: {TEMPLATE} nije pronađen!")
    sys.exit(1)

shutil.copy(TEMPLATE, TEMPLATE.with_suffix(".html.bak_dedup"))
text = TEMPLATE.read_text(encoding="utf-8")

# Pronađi sve <script> blokove koji sadrže invSort
# i ostavi samo prvi, drugi obriši
script_pattern = re.compile(
    r'<script>\s*\n'           # početak <script>
    r'(?:.*\n)*?'              # bilo koji sadržaj
    r'.*let _invSortDir.*\n'   # mora sadržavati _invSortDir
    r'(?:.*\n)*?'
    r'.*</script>',            # kraj </script>
    re.MULTILINE
)

matches = list(script_pattern.finditer(text))
print(f"Pronađeno {len(matches)} script blokova s _invSortDir")

if len(matches) >= 2:
    # Obriši drugi match (zadnji pronađeni)
    second = matches[-1]
    text = text[:second.start()] + text[second.end():]
    TEMPLATE.write_text(text, encoding="utf-8")
    print("✅ Dupli script blok uklonjen!")
    
    # Provjera
    remaining = list(script_pattern.finditer(text))
    print(f"✅ Ostalo {len(remaining)} script blokova s _invSortDir")
elif len(matches) == 1:
    print("ℹ️  Samo jedan blok pronađen — nema duplikata, ništa nije promijenjeno")
else:
    print("⚠️  Nije pronađen niti jedan blok s _invSortDir!")

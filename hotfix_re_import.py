#!/usr/bin/env python3
"""Hotfix: dodaj 'import re' unutar _parse_date_sort jer re nije dostupan globalno."""

import shutil
from pathlib import Path

APP = Path("app.py")
shutil.copy(APP, APP.with_suffix(".py.bak_re"))

text = APP.read_text(encoding="utf-8")

OLD = '''def _parse_date_sort(s):
    """Parsira datum u usporedivi tuple (god, mj, dan) za sortiranje.
    Podržava: YYYY-MM-DD, DD.MM.YYYY, D.M.YYYY i varijante s točkama."""
    if not s:
        return (0, 0, 0)
    s = str(s).strip().rstrip('.')'''

NEW = '''def _parse_date_sort(s):
    """Parsira datum u usporedivi tuple (god, mj, dan) za sortiranje.
    Podržava: YYYY-MM-DD, DD.MM.YYYY, D.M.YYYY i varijante s točkama."""
    import re
    if not s:
        return (0, 0, 0)
    s = str(s).strip().rstrip('.')'''

if OLD in text:
    text = text.replace(OLD, NEW)
    APP.write_text(text, encoding="utf-8")
    print("✅ import re dodan unutar _parse_date_sort()")
else:
    print("⚠️  Funkcija nije pronađena — provjeri ručno!")

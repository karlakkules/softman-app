#!/usr/bin/env python3
"""
add_zip_btn_form.py
Dodaje ZIP gumb u topbar form.html za odobrene putne naloge,
između gumba "Natrag" i "PDF".

Pokretanje:
    cd ~/Projects/Softman_app
    python3 add_zip_btn_form.py
"""

import shutil
import os

FORM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'form.html')
BAK_PATH = FORM_PATH + '.bak_zip_btn'

ZIP_BTN = '''<a href="/orders/{{ order.id }}/zip" class="btn btn-secondary" title="Preuzmi ZIP (PDF + računi)" style="width:30px;height:30px;padding:0;display:inline-flex;align-items:center;justify-content:center;">
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="2" y="1" width="12" height="14" rx="1.5" fill="#f5f5f5" stroke="#bbb" stroke-width="0.8"/>
    <rect x="5" y="1" width="2" height="4" fill="#ddd" stroke="#bbb" stroke-width="0.5"/>
    <rect x="9" y="1" width="2" height="4" fill="#ddd" stroke="#bbb" stroke-width="0.5"/>
    <rect x="5" y="5" width="2" height="2" fill="#bbb"/>
    <rect x="9" y="5" width="2" height="2" fill="#bbb"/>
    <rect x="5" y="7" width="2" height="2" fill="#ddd"/>
    <rect x="9" y="7" width="2" height="2" fill="#ddd"/>
    <rect x="5" y="9" width="2" height="2" fill="#bbb"/>
    <rect x="9" y="9" width="2" height="2" fill="#bbb"/>
    <text x="3.5" y="14.5" font-family="Arial" font-size="4" font-weight="bold" fill="#555">ZIP</text>
  </svg>
</a>
'''

# Stari blok za approved (PDF + Vrati u postupak)
OLD_APPROVED = '''{% if order and order.status == 'approved' %}
<a href="/orders/{{ order.id }}/pdf" target="_blank" class="btn btn-secondary" title="Preuzmi PDF putnog naloga">
  🖨️ PDF
</a>
<button class="btn btn-secondary" onclick="saveOrder('rejected')">
  ↩️ <span data-hr="Vrati u postupak" data-en="Return for review">Vrati u postupak</span>
</button>
{% endif %}'''

NEW_APPROVED = '''{% if order and order.status == 'approved' %}
''' + ZIP_BTN + '''<a href="/orders/{{ order.id }}/pdf" target="_blank" class="btn btn-secondary" title="Preuzmi PDF putnog naloga">
  🖨️ PDF
</a>
<button class="btn btn-secondary" onclick="saveOrder('rejected')">
  ↩️ <span data-hr="Vrati u postupak" data-en="Return for review">Vrati u postupak</span>
</button>
{% endif %}'''

# Pokušaj i za status knjizeno (ako postoji isti blok)
OLD_KNJIZENO = '''{% if order and order.status in ['approved', 'knjizeno'] %}
<a href="/orders/{{ order.id }}/pdf" target="_blank" class="btn btn-secondary" title="Preuzmi PDF putnog naloga">
  🖨️ PDF
</a>'''

NEW_KNJIZENO = '''{% if order and order.status in ['approved', 'knjizeno'] %}
''' + ZIP_BTN + '''<a href="/orders/{{ order.id }}/pdf" target="_blank" class="btn btn-secondary" title="Preuzmi PDF putnog naloga">
  🖨️ PDF
</a>'''

def patch():
    with open(FORM_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    # Provjeri je li već patchano
    if '/orders/{{ order.id }}/zip' in content:
        print("INFO: ZIP gumb već postoji u form.html — nema što dodati.")
        return True

    # Pokušaj s approved blokom
    if OLD_APPROVED in content:
        content = content.replace(OLD_APPROVED, NEW_APPROVED, 1)
        changed = True
        print("OK: ZIP gumb dodan za status 'approved'.")
    elif OLD_KNJIZENO in content:
        content = content.replace(OLD_KNJIZENO, NEW_KNJIZENO, 1)
        changed = True
        print("OK: ZIP gumb dodan za status 'approved'/'knjizeno'.")
    else:
        # Fallback: pronađi PDF link i dodaj ZIP ispred njega
        old_pdf = '''<a href="/orders/{{ order.id }}/pdf" target="_blank" class="btn btn-secondary" title="Preuzmi PDF putnog naloga">
  🖨️ PDF
</a>'''
        new_pdf = ZIP_BTN + old_pdf
        if old_pdf in content:
            content = content.replace(old_pdf, new_pdf, 1)
            changed = True
            print("OK: ZIP gumb dodan ispred PDF gumba (fallback metoda).")
        else:
            print("GREŠKA: Ne mogu pronaći PDF gumb u topbar sekciji form.html.")
            print("  Provjeri form.html ručno i dodaj ZIP gumb ispred PDF gumba.")
            return False

    if changed:
        shutil.copy2(FORM_PATH, BAK_PATH)
        print(f"OK: Backup spremljen → {BAK_PATH}")
        with open(FORM_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print("OK: templates/form.html ažuriran.")
        print()
        print("Restartaj Flask i provjeri PN s statusom 'Odobreno'.")

    return True

if __name__ == '__main__':
    patch()

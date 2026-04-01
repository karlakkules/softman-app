#!/usr/bin/env python3
"""
fix_zip_btn.py
1. Dodaje /orders/<id>/export-zip rutu u app.py
2. Popravlja ZIP gumb u form.html (ispravna ikona 📦, ispravna ruta)

Pokretanje:
    cd ~/Projects/Softman_app
    python3 fix_zip_btn.py
"""

import shutil
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
APP_PATH = os.path.join(BASE, 'app.py')
FORM_PATH = os.path.join(BASE, 'templates', 'form.html')

# ─────────────────────────────────────────────────────────────────────────────
# 1. DODAJ RUTU U app.py
# ─────────────────────────────────────────────────────────────────────────────

ZIP_ROUTE = '''
@app.route('/orders/<int:order_id>/export-zip')
@require_perm('can_view_orders')
def export_order_zip(order_id):
    """Preuzmi ZIP arhivu: PDF putnog naloga + svi priloženi dokumenti troškova."""
    import zipfile
    audit('export_zip', module='putni_nalozi', entity='travel_order', entity_id=order_id)
    conn = get_db()
    order = conn.execute("SELECT * FROM travel_orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return "Not found", 404
    if order['status'] not in ['approved', 'knjizeno']:
        conn.close()
        return "ZIP nije dostupan. Nalog mora biti odobren.", 404

    zip_buffer = io.BytesIO()
    auto_id_safe = str(order['auto_id']).replace('/', '-')

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # ── PDF putnog naloga ──
        pdf_added = False
        if order['pdf_path']:
            pdf_path_full = os.path.join(os.path.dirname(__file__), 'pdfs', order['pdf_path'])
            if os.path.exists(pdf_path_full):
                zf.write(pdf_path_full, f"PN_{auto_id_safe}.pdf")
                pdf_added = True

        if not pdf_added:
            # Generiraj PDF on-the-fly
            expenses = conn.execute(
                """SELECT e.*, ec.name as cat_name FROM expenses e
                   LEFT JOIN expense_categories ec ON e.category_id = ec.id
                   WHERE e.travel_order_id=? ORDER BY e.sort_order""", (order_id,)
            ).fetchall()
            employee = conn.execute("SELECT * FROM employees WHERE id=?", (order['employee_id'],)).fetchone() if order['employee_id'] else None
            vehicle = conn.execute("SELECT * FROM vehicles WHERE id=?", (order['vehicle_id'],)).fetchone() if order['vehicle_id'] else None
            approved_by = conn.execute("SELECT * FROM employees WHERE id=?", (order['approved_by_id'],)).fetchone() if order['approved_by_id'] else None
            validator = conn.execute("SELECT * FROM employees WHERE id=?", (order['validator_id'],)).fetchone() if order['validator_id'] else None
            blagajnik = conn.execute("SELECT * FROM employees WHERE is_blagajnik=1 LIMIT 1").fetchone()
            knjizio = conn.execute("SELECT * FROM employees WHERE is_knjizio=1 LIMIT 1").fetchone()
            settings_rows = {row['key']: row['value'] for row in conn.execute("SELECT * FROM settings").fetchall()}
            pdf_buf = create_pdf(dict(order), list(expenses),
                                 row_to_dict(employee), row_to_dict(vehicle),
                                 row_to_dict(approved_by), row_to_dict(validator),
                                 row_to_dict(blagajnik), row_to_dict(knjizio), settings_rows)
            zf.writestr(f"PN_{auto_id_safe}.pdf", pdf_buf.read())

        # ── Priloženi dokumenti troškova (pn_expenses) ──
        try:
            pn_expenses = conn.execute(
                "SELECT * FROM pn_expenses WHERE travel_order_id=? ORDER BY id", (order_id,)
            ).fetchall()
            storage_row = conn.execute("SELECT value FROM settings WHERE key='invoice_storage_path'").fetchone()
            storage_base = storage_row['value'] if storage_row and storage_row['value'] else os.path.join(os.path.dirname(__file__), 'uploads', 'racuni')

            added_names = set()
            for i, exp in enumerate(pn_expenses, 1):
                stored = exp['stored_filename'] if 'stored_filename' in exp.keys() else None
                stored_path = exp['stored_path'] if 'stored_path' in exp.keys() else None
                if not stored:
                    continue
                # Pokušaj različite lokacije
                candidates = []
                if stored_path and os.path.isabs(stored_path) and os.path.exists(stored_path):
                    candidates.append(stored_path)
                candidates.append(os.path.join(storage_base, stored))
                candidates.append(os.path.join(os.path.dirname(__file__), 'uploads', 'racuni', stored))
                candidates.append(os.path.join(os.path.dirname(__file__), 'uploads', stored))

                file_path = None
                for c in candidates:
                    if os.path.exists(c):
                        file_path = c
                        break

                if file_path:
                    ext = os.path.splitext(stored)[1]
                    zip_name = f"trosak_{i:02d}{ext}"
                    # Izbjegni duplikate
                    base_zip_name = zip_name
                    counter = 1
                    while zip_name in added_names:
                        zip_name = f"{os.path.splitext(base_zip_name)[0]}_{counter}{ext}"
                        counter += 1
                    added_names.add(zip_name)
                    zf.write(file_path, zip_name)
        except Exception:
            pass  # pn_expenses tablica možda ne postoji — ZIP i dalje radi s PDF-om

    conn.close()
    zip_buffer.seek(0)
    filename = f"PN_{auto_id_safe}.zip"
    return send_file(zip_buffer, mimetype='application/zip',
                     download_name=filename, as_attachment=True)

'''

def patch_app():
    with open(APP_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'export_order_zip' in content:
        print("INFO: export_order_zip ruta već postoji — preskačem.")
        return True

    # Dodaj rutu ispred generate_pdf rute ili na kraj ruta sekcije
    anchor = "@app.route('/orders/<int:order_id>/pdf')"
    if anchor in content:
        content = content.replace(anchor, ZIP_ROUTE + anchor, 1)
        print("OK: ZIP ruta dodana u app.py (ispred /pdf rute).")
    else:
        # Fallback — dodaj ispred def create_pdf
        anchor2 = "def create_pdf("
        if anchor2 in content:
            content = content.replace(anchor2, ZIP_ROUTE + "def create_pdf(", 1)
            print("OK: ZIP ruta dodana u app.py (ispred create_pdf).")
        else:
            print("GREŠKA: Ne mogu pronaći mjesto za umetanje ZIP rute.")
            return False

    shutil.copy2(APP_PATH, APP_PATH + '.bak_zip_route')
    with open(APP_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"OK: app.py ažuriran. Backup → app.py.bak_zip_route")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 2. POPRAVI ZIP GUMB U form.html
# ─────────────────────────────────────────────────────────────────────────────

# Točna ikona i ruta kao u orders.html listi
ZIP_BTN_CORRECT = '<a href="/orders/{{ order.id }}/export-zip" class="btn btn-secondary" style="width:30px;height:30px;padding:0;display:inline-flex;align-items:center;justify-content:center;" title="Preuzmi ZIP (PDF naloga + dokumenti troškova)">📦</a>\n'

def patch_form():
    with open(FORM_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Ukloni stari (krivi) ZIP gumb koji je mogao biti dodan prethodnom skriptom
    # Prepoznajemo ga po /orders/{{ order.id }}/zip (stara ruta)
    old_zip_pattern = re.compile(
        r'<a href="/orders/\{\{ order\.id \}\}/zip"[^>]*>.*?</a>\s*\n?',
        re.DOTALL
    )
    content_new = old_zip_pattern.sub('', content)
    if content_new != content:
        print("OK: Stari ZIP gumb (kriva ruta) uklonjen iz form.html.")
        content = content_new

    # Provjeri je li ispravni gumb već tu
    if '/orders/{{ order.id }}/export-zip' in content:
        print("INFO: Ispravni ZIP gumb već postoji u form.html.")
        return True

    # Dodaj ZIP gumb ispred PDF linka za approved status
    old_pdf_link = '<a href="/orders/{{ order.id }}/pdf" target="_blank" class="btn btn-secondary" title="Preuzmi PDF putnog naloga">'
    if old_pdf_link in content:
        content = content.replace(old_pdf_link, ZIP_BTN_CORRECT + old_pdf_link, 1)
        print("OK: ZIP gumb (📦, ispravna ruta) dodan ispred PDF gumba u form.html.")
    else:
        # Fallback: traži varijante PDF linka
        alt = '<a href="/orders/{{ order.id }}/pdf"'
        if alt in content:
            content = content.replace(alt, ZIP_BTN_CORRECT + alt, 1)
            print("OK: ZIP gumb dodan (fallback) u form.html.")
        else:
            print("GREŠKA: Ne mogu pronaći PDF gumb u form.html.")
            return False

    shutil.copy2(FORM_PATH, FORM_PATH + '.bak_zip_btn2')
    with open(FORM_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"OK: templates/form.html ažuriran. Backup → form.html.bak_zip_btn2")
    return True


if __name__ == '__main__':
    ok1 = patch_app()
    ok2 = patch_form()
    print()
    if ok1 and ok2:
        print("✅ Sve OK — restartaj Flask i testiraj ZIP gumb na odobrenom nalogu.")
    else:
        print("⚠️  Neke promjene nisu primijenjene — provjeri poruke gore.")

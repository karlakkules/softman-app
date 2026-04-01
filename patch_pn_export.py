#!/usr/bin/env python3
"""
Patch: 2 fixa za putne naloge
1. app.py: create_pdf i _generate_and_save_pdf čitaju iz pn_expenses umjesto expenses
2. app.py: novi ZIP export endpoint /orders/<id>/export-zip
3. orders.html: ZIP gumb za odobrene/knjižene naloge
"""
import shutil
from pathlib import Path

errors = []

# ════════════════════════════════════════════════════════
# app.py
# ════════════════════════════════════════════════════════
APP = Path('app.py')
if not APP.exists():
    print('ERROR: app.py nije pronađen!'); exit(1)

shutil.copy(APP, APP.with_suffix('.py.bak'))
c = APP.read_text(encoding='utf-8')

# ── Fix 1a: _generate_and_save_pdf — čitaj iz pn_expenses ──────────────────
OLD_GEN = """    expenses = conn.execute('''SELECT e.*, ec.name as cat_name FROM expenses e
                               LEFT JOIN expense_categories ec ON e.category_id = ec.id
                               WHERE e.travel_order_id=? ORDER BY e.sort_order''', (order_id,)).fetchall()
    employee = conn.execute("SELECT * FROM employees WHERE id=?", (order['employee_id'],)).fetchone() if order['employee_id'] else None
    vehicle = conn.execute("SELECT * FROM vehicles WHERE id=?", (order['vehicle_id'],)).fetchone() if order['vehicle_id'] else None
    approved_by = conn.execute("SELECT * FROM employees WHERE id=?", (order['approved_by_id'],)).fetchone() if order['approved_by_id'] else None
    validator = conn.execute("SELECT * FROM employees WHERE id=?", (order['validator_id'],)).fetchone() if order['validator_id'] else None
    blagajnik = conn.execute("SELECT * FROM employees WHERE is_blagajnik=1 LIMIT 1").fetchone()
    knjizio = conn.execute("SELECT * FROM employees WHERE is_knjizio=1 LIMIT 1").fetchone()
    settings = {row['key']: row['value'] for row in conn.execute("SELECT * FROM settings").fetchall()}
    pdf_buffer = create_pdf(dict(order), list(expenses),
                           row_to_dict(employee), row_to_dict(vehicle),
                           row_to_dict(approved_by), row_to_dict(validator),
                           row_to_dict(blagajnik), row_to_dict(knjizio), settings)
    pdf_filename = f"PN_{order['auto_id']}.pdf"
    pdf_folder = os.path.join(os.path.dirname(__file__), 'pdfs')"""

NEW_GEN = """    expenses = conn.execute('''SELECT pe.*, ec.name as cat_name,
                               pe.payment_method as paid_privately_method,
                               CASE WHEN pe.payment_method='private' THEN 1 ELSE 0 END as paid_privately,
                               pe.amount as amount, pe.description as description
                               FROM pn_expenses pe
                               LEFT JOIN expense_categories ec ON pe.category_id = ec.id
                               WHERE pe.travel_order_id=? ORDER BY pe.doc_date, pe.created_at''', (order_id,)).fetchall()
    employee = conn.execute("SELECT * FROM employees WHERE id=?", (order['employee_id'],)).fetchone() if order['employee_id'] else None
    vehicle = conn.execute("SELECT * FROM vehicles WHERE id=?", (order['vehicle_id'],)).fetchone() if order['vehicle_id'] else None
    approved_by = conn.execute("SELECT * FROM employees WHERE id=?", (order['approved_by_id'],)).fetchone() if order['approved_by_id'] else None
    validator = conn.execute("SELECT * FROM employees WHERE id=?", (order['validator_id'],)).fetchone() if order['validator_id'] else None
    blagajnik = conn.execute("SELECT * FROM employees WHERE is_blagajnik=1 LIMIT 1").fetchone()
    knjizio = conn.execute("SELECT * FROM employees WHERE is_knjizio=1 LIMIT 1").fetchone()
    settings = {row['key']: row['value'] for row in conn.execute("SELECT * FROM settings").fetchall()}
    pdf_buffer = create_pdf(dict(order), list(expenses),
                           row_to_dict(employee), row_to_dict(vehicle),
                           row_to_dict(approved_by), row_to_dict(validator),
                           row_to_dict(blagajnik), row_to_dict(knjizio), settings)
    pdf_filename = f"PN_{order['auto_id']}.pdf"
    pdf_folder = os.path.join(os.path.dirname(__file__), 'pdfs')"""

if OLD_GEN in c:
    c = c.replace(OLD_GEN, NEW_GEN)
    print('✅ Fix 1a: _generate_and_save_pdf čita iz pn_expenses')
else:
    errors.append('Fix 1a: _generate_and_save_pdf pattern nije pronađen')

# ── Fix 1b: generate_pdf (on-the-fly) — čitaj iz pn_expenses ───────────────
OLD_PDF = """    expenses = conn.execute('''SELECT e.*, ec.name as cat_name FROM expenses e
                               LEFT JOIN expense_categories ec ON e.category_id = ec.id
                               WHERE e.travel_order_id=? ORDER BY e.sort_order''', (order_id,)).fetchall()
    employee = conn.execute("SELECT * FROM employees WHERE id=?", (order['employee_id'],)).fetchone() if order['employee_id'] else None
    vehicle = conn.execute("SELECT * FROM vehicles WHERE id=?", (order['vehicle_id'],)).fetchone() if order['vehicle_id'] else None
    approved_by = conn.execute("SELECT * FROM employees WHERE id=?", (order['approved_by_id'],)).fetchone() if order['approved_by_id'] else None
    validator = conn.execute("SELECT * FROM employees WHERE id=?", (order['validator_id'],)).fetchone() if order['validator_id'] else None
    blagajnik = conn.execute("SELECT * FROM employees WHERE is_blagajnik=1 LIMIT 1").fetchone()
    knjizio = conn.execute("SELECT * FROM employees WHERE is_knjizio=1 LIMIT 1").fetchone()
    settings = {row['key']: row['value'] for row in conn.execute("SELECT * FROM settings").fetchall()}
    conn.close()
    pdf_buffer = create_pdf(dict(order), list(expenses),
                           row_to_dict(employee), row_to_dict(vehicle),
                           row_to_dict(approved_by), row_to_dict(validator),
                           row_to_dict(blagajnik), row_to_dict(knjizio), settings)
    filename = f"PN_{order['auto_id']}.pdf"
    return send_file(pdf_buffer, mimetype='application/pdf', download_name=filename, as_attachment=False)"""

NEW_PDF = """    expenses = conn.execute('''SELECT pe.*, ec.name as cat_name,
                               CASE WHEN pe.payment_method='private' THEN 1 ELSE 0 END as paid_privately,
                               pe.amount as amount, pe.description as description
                               FROM pn_expenses pe
                               LEFT JOIN expense_categories ec ON pe.category_id = ec.id
                               WHERE pe.travel_order_id=? ORDER BY pe.doc_date, pe.created_at''', (order_id,)).fetchall()
    employee = conn.execute("SELECT * FROM employees WHERE id=?", (order['employee_id'],)).fetchone() if order['employee_id'] else None
    vehicle = conn.execute("SELECT * FROM vehicles WHERE id=?", (order['vehicle_id'],)).fetchone() if order['vehicle_id'] else None
    approved_by = conn.execute("SELECT * FROM employees WHERE id=?", (order['approved_by_id'],)).fetchone() if order['approved_by_id'] else None
    validator = conn.execute("SELECT * FROM employees WHERE id=?", (order['validator_id'],)).fetchone() if order['validator_id'] else None
    blagajnik = conn.execute("SELECT * FROM employees WHERE is_blagajnik=1 LIMIT 1").fetchone()
    knjizio = conn.execute("SELECT * FROM employees WHERE is_knjizio=1 LIMIT 1").fetchone()
    settings = {row['key']: row['value'] for row in conn.execute("SELECT * FROM settings").fetchall()}
    conn.close()
    pdf_buffer = create_pdf(dict(order), list(expenses),
                           row_to_dict(employee), row_to_dict(vehicle),
                           row_to_dict(approved_by), row_to_dict(validator),
                           row_to_dict(blagajnik), row_to_dict(knjizio), settings)
    filename = f"PN_{order['auto_id']}.pdf"
    return send_file(pdf_buffer, mimetype='application/pdf', download_name=filename, as_attachment=False)"""

if OLD_PDF in c:
    c = c.replace(OLD_PDF, NEW_PDF)
    print('✅ Fix 1b: generate_pdf (on-the-fly) čita iz pn_expenses')
else:
    errors.append('Fix 1b: generate_pdf pattern nije pronađen')

# ── Fix 2: ZIP export endpoint ───────────────────────────────────────────────
ZIP_ENDPOINT = '''
@app.route('/orders/<int:order_id>/export-zip')
@require_perm('can_view_orders')
def export_order_zip(order_id):
    """ZIP arhiva: PDF putnog naloga + svi PDF troškovi iz pn_expenses."""
    import zipfile, io as _io
    audit('export_zip', module='putni_nalozi', entity='travel_order', entity_id=order_id)
    conn = get_db()
    order = conn.execute("SELECT * FROM travel_orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return "Not found", 404
    if order['status'] not in ['approved', 'knjizeno']:
        conn.close()
        return "ZIP nije dostupan. Nalog mora biti odobren.", 404

    # Generiraj PDF putnog naloga
    expenses = conn.execute("""SELECT pe.*, ec.name as cat_name,
        CASE WHEN pe.payment_method='private' THEN 1 ELSE 0 END as paid_privately,
        pe.amount as amount, pe.description as description
        FROM pn_expenses pe
        LEFT JOIN expense_categories ec ON pe.category_id = ec.id
        WHERE pe.travel_order_id=? ORDER BY pe.doc_date, pe.created_at""", (order_id,)).fetchall()
    pn_exp_docs = conn.execute("""SELECT pe.stored_path, pe.original_filename, pe.description,
        ec.name as cat_name, pe.doc_date
        FROM pn_expenses pe
        LEFT JOIN expense_categories ec ON pe.category_id = ec.id
        WHERE pe.travel_order_id=? AND pe.stored_path IS NOT NULL AND pe.stored_path != ''
        ORDER BY pe.doc_date, pe.created_at""", (order_id,)).fetchall()
    employee    = conn.execute("SELECT * FROM employees WHERE id=?", (order['employee_id'],)).fetchone() if order['employee_id'] else None
    vehicle     = conn.execute("SELECT * FROM vehicles WHERE id=?", (order['vehicle_id'],)).fetchone() if order['vehicle_id'] else None
    approved_by = conn.execute("SELECT * FROM employees WHERE id=?", (order['approved_by_id'],)).fetchone() if order['approved_by_id'] else None
    validator   = conn.execute("SELECT * FROM employees WHERE id=?", (order['validator_id'],)).fetchone() if order['validator_id'] else None
    blagajnik   = conn.execute("SELECT * FROM employees WHERE is_blagajnik=1 LIMIT 1").fetchone()
    knjizio     = conn.execute("SELECT * FROM employees WHERE is_knjizio=1 LIMIT 1").fetchone()
    settings    = {row['key']: row['value'] for row in conn.execute("SELECT * FROM settings").fetchall()}
    conn.close()

    pdf_buf = create_pdf(dict(order), list(expenses),
                         row_to_dict(employee), row_to_dict(vehicle),
                         row_to_dict(approved_by), row_to_dict(validator),
                         row_to_dict(blagajnik), row_to_dict(knjizio), settings)

    # Napravi ZIP
    zip_buf = _io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. PDF putnog naloga
        zf.writestr(f"PN_{order['auto_id']}.pdf", pdf_buf.read())

        # 2. PDF troškovi iz pn_expenses
        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        seen = set()
        for i, doc in enumerate(pn_exp_docs, 1):
            sp = doc['stored_path']
            if not sp:
                continue
            # stored_path može biti apsolutni ili relativan
            full = sp if os.path.isabs(sp) else os.path.join(upload_dir, sp)
            if not os.path.exists(full):
                continue
            ext = os.path.splitext(full)[1].lower() or '.pdf'
            # Ime datoteke u ZIPu: redni_broj_kategorija_datum.ext
            cat  = (doc['cat_name'] or 'trosak').replace(' ', '_')
            date = (doc['doc_date'] or '').replace('-', '')
            base = f"{i:02d}_{cat}_{date}{ext}"
            # izbjegni duplikate
            if base in seen:
                base = f"{i:02d}_{cat}_{date}_{i}{ext}"
            seen.add(base)
            with open(full, 'rb') as fh:
                zf.writestr(f"troskovi/{base}", fh.read())

    zip_buf.seek(0)
    zip_name = f"PN_{order['auto_id']}_export.zip"
    return send_file(zip_buf, mimetype='application/zip', download_name=zip_name, as_attachment=True)

'''

# Ubaci endpoint ispred generate_pdf rute
MARKER_ZIP = "@app.route('/orders/<int:order_id>/pdf')\n@require_perm('can_view_orders')\ndef generate_pdf(order_id):"
if MARKER_ZIP in c:
    c = c.replace(MARKER_ZIP, ZIP_ENDPOINT + MARKER_ZIP)
    print('✅ Fix 2: ZIP export endpoint dodan')
else:
    errors.append('Fix 2: marker za ZIP endpoint nije pronađen')

APP.write_text(c, encoding='utf-8')

# ════════════════════════════════════════════════════════
# orders.html — ZIP gumb
# ════════════════════════════════════════════════════════
TORD = Path('templates/orders.html')
if not TORD.exists():
    errors.append('templates/orders.html ne postoji')
else:
    shutil.copy(TORD, TORD.with_suffix('.html.bak'))
    oc = TORD.read_text(encoding='utf-8')

    OLD_BTN = """                {% if o.status in ["approved", "knjizeno"] %}
                  <a href="/orders/{{ o.id }}/pdf" target="_blank" class="btn btn-sm btn-secondary" style="width:30px;height:30px;padding:0;display:flex;align-items:center;justify-content:center;" title="Preuzmi PDF"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M3 1h7l3 3v10a1 1 0 01-1 1H3a1 1 0 01-1-1V2a1 1 0 011-1z" fill="#e74c3c" stroke="#c0392b" stroke-width="0.5"/>
  <path d="M10 1l3 3h-3V1z" fill="#c0392b"/>
  <text x="3.5" y="11.5" font-family="Arial" font-size="4.5" font-weight="bold" fill="white">PDF</text>
</svg></a>
                  <button style="width:30px;height:30px;padding:0;background:#f5f5f5;color:#444;border:1px solid #ccc;border-radius:6px;cursor:pointer;font-size:14px;" onclick="printOrder({{ o.id }})" title="Ispiši nalog">🖨️</button>"""

    NEW_BTN = """                {% if o.status in ["approved", "knjizeno"] %}
                  <a href="/orders/{{ o.id }}/pdf" target="_blank" class="btn btn-sm btn-secondary" style="width:30px;height:30px;padding:0;display:flex;align-items:center;justify-content:center;" title="Preuzmi PDF"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M3 1h7l3 3v10a1 1 0 01-1 1H3a1 1 0 01-1-1V2a1 1 0 011-1z" fill="#e74c3c" stroke="#c0392b" stroke-width="0.5"/>
  <path d="M10 1l3 3h-3V1z" fill="#c0392b"/>
  <text x="3.5" y="11.5" font-family="Arial" font-size="4.5" font-weight="bold" fill="white">PDF</text>
</svg></a>
                  <a href="/orders/{{ o.id }}/export-zip" class="btn btn-sm btn-secondary" style="width:30px;height:30px;padding:0;display:flex;align-items:center;justify-content:center;" title="Preuzmi ZIP (PDF naloga + dokumenti troškova)">📦</a>
                  <button style="width:30px;height:30px;padding:0;background:#f5f5f5;color:#444;border:1px solid #ccc;border-radius:6px;cursor:pointer;font-size:14px;" onclick="printOrder({{ o.id }})" title="Ispiši nalog">🖨️</button>"""

    if OLD_BTN in oc:
        oc = oc.replace(OLD_BTN, NEW_BTN)
        print('✅ Fix 3: ZIP gumb dodan u orders.html')
    else:
        errors.append('Fix 3: orders.html gumb pattern nije pronađen')

    TORD.write_text(oc, encoding='utf-8')

print()
if errors:
    print('⚠️  NISU primijenjeni:')
    for e in errors: print(f'   ❌ {e}')
else:
    print('✅ Svi patchi primijenjeni!')
    print('\nTestiraj:')
    print('  1. Otvori odobreni PN → PDF → Ostali troškovi trebaju prikazati podatke')
    print('  2. U listi naloga → odobreni PN → klikni 📦 → ZIP s PDF-om i dokumentima')

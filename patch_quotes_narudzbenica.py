#!/usr/bin/env python3
"""
Patch: app.py — dodaje:
  1. Stupac narudzbenica_path u tablicu quotes (migracija)
  2. POST /api/quotes/<id>/narudzbenica  — upload PDF narudžbenice
  3. GET  /quotes/<id>/narudzbenica      — serve narudžbenice
  4. Vraća narudzbenica_path u quotes_list ruti
"""
import os, shutil, re

BASE = os.path.expanduser('~/Projects/Softman_app')
APP  = os.path.join(BASE, 'app.py')
BACKUP_DIR = os.path.join(BASE, '.backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

bak = os.path.join(BACKUP_DIR, 'app.py.bak_narudzbenica')
shutil.copy2(APP, bak)
print(f'✅ Backup: {bak}')

with open(APP, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. DB migracija — stupac narudzbenica_path ────────────────────────────
MIGA = "# Migration: create quotes table"
MIGB = """# Migration: narudzbenica_path u quotes
    try:
        c.execute("ALTER TABLE quotes ADD COLUMN narudzbenica_path TEXT")
        print("Migration: quotes.narudzbenica_path added")
    except: pass

    # Migration: create quotes table"""

if MIGB not in content and MIGA in content:
    content = content.replace(MIGA, MIGB, 1)
    changes += 1
    print('✅ Migracija narudzbenica_path dodana')
else:
    print('⚠️  Migracija već postoji ili marker nije pronađen')

# ── 2. quotes_list ruta — dodaj narudzbenica_path u SELECT ────────────────
# Tražimo SELECT * FROM quotes u quotes_list ruti
OLD_SEL = "SELECT q.*, c.name as client_name FROM quotes q"
NEW_SEL = "SELECT q.*, c.name as client_name, q.narudzbenica_path FROM quotes q"

if NEW_SEL not in content and OLD_SEL in content:
    content = content.replace(OLD_SEL, NEW_SEL, 1)
    changes += 1
    print('✅ narudzbenica_path dodan u quotes SELECT')
else:
    # Ako je samo SELECT * FROM quotes
    OLD_SEL2 = "SELECT * FROM quotes ORDER BY"
    NEW_SEL2 = "SELECT *, narudzbenica_path FROM quotes ORDER BY"
    if NEW_SEL2 not in content and OLD_SEL2 in content:
        content = content.replace(OLD_SEL2, NEW_SEL2, 1)
        changes += 1
        print('✅ narudzbenica_path dodan u quotes SELECT (fallback)')
    else:
        print('⚠️  quotes SELECT nije modificiran — provjeri ručno (možda već OK ako je SELECT *)')

# ── 3. Nove Flask rute — ubaci prije @app.route('/api/quotes/<int:quote_id>', methods=['DELETE']) ──
NEW_ROUTES = '''
@app.route('/api/quotes/<int:quote_id>/narudzbenica', methods=['POST'])
@require_perm('can_edit_quotes')
def upload_quote_narudzbenica(quote_id):
    """Upload narudžbenice za ponudu — sprema kao Narudzbenica_<auto_id>.pdf"""
    import os
    from datetime import datetime as dt

    if 'file' not in request.files:
        return jsonify({'error': 'Nema datoteke'}), 400
    f = request.files['file']
    if not f.filename or not f.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Prihvaćaju se samo PDF datoteke'}), 400

    conn = get_db()
    quote = conn.execute("SELECT * FROM quotes WHERE id=?", (quote_id,)).fetchone()
    if not quote:
        conn.close()
        return jsonify({'error': 'Ponuda nije pronađena'}), 404

    auto_id = quote['auto_id']
    pdf_folder = os.path.join(os.path.dirname(__file__), 'pdfs')
    os.makedirs(pdf_folder, exist_ok=True)

    filename = f"Narudzbenica_{auto_id}.pdf"
    dest = os.path.join(pdf_folder, filename)

    # Ako već postoji, zamijeni
    f.save(dest)

    conn.execute("UPDATE quotes SET narudzbenica_path=?, updated_at=? WHERE id=?",
                 (filename, dt.now().isoformat(), quote_id))
    conn.commit()
    conn.close()
    audit('upload', module='ponude', entity='quote', entity_id=quote_id,
          detail=f'Narudžbenica priložena: {filename}')
    return jsonify({'success': True, 'filename': filename})


@app.route('/quotes/<int:quote_id>/narudzbenica')
@require_perm('can_view_quotes')
def serve_quote_narudzbenica(quote_id):
    """Serve narudžbenice PDF za ponudu."""
    import os
    conn = get_db()
    quote = conn.execute("SELECT narudzbenica_path FROM quotes WHERE id=?", (quote_id,)).fetchone()
    conn.close()
    if not quote or not quote['narudzbenica_path']:
        return "Narudžbenica nije priložena", 404
    pdf_folder = os.path.join(os.path.dirname(__file__), 'pdfs')
    path = os.path.join(pdf_folder, quote['narudzbenica_path'])
    if not os.path.exists(path):
        return "Datoteka nije pronađena", 404
    return send_file(path, mimetype='application/pdf',
                     download_name=quote['narudzbenica_path'], as_attachment=False)

'''

ANCHOR_DELETE = "@app.route('/api/quotes/<int:quote_id>', methods=['DELETE'])"

if "/api/quotes/<int:quote_id>/narudzbenica" not in content and ANCHOR_DELETE in content:
    content = content.replace(ANCHOR_DELETE, NEW_ROUTES + ANCHOR_DELETE, 1)
    changes += 1
    print('✅ Flask rute za narudžbenicu dodane')
else:
    print('⚠️  Rute već postoje ili anchor nije pronađen')

with open(APP, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n{"✅ Patch gotov" if changes else "❌ Bez promjena"} ({changes} izmjena)')
print('\nSljedeći koraci:')
print('  1. Kopiraj quotes_list.html i quotes_form.html u templates/')
print('  2. Restart Flask servera')

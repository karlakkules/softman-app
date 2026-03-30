#!/usr/bin/env python3
"""
Patch: zamijeni @admin_required s @api_login_required + JSON 403
na supplier POST, PUT, DELETE rutama u app.py
"""
import shutil, os, sys

APP = os.path.join(os.path.dirname(__file__), 'app.py')

if not os.path.exists(APP):
    print("❌ Nije pronađen app.py u istom direktoriju!")
    sys.exit(1)

shutil.copy(APP, APP + '.bak')
print("✅ Backup kreiran: app.py.bak")

with open(APP, 'r', encoding='utf-8') as f:
    src = f.read()

# --- Patch 1: supplier_create (POST) ---
OLD1 = """@app.route('/api/suppliers', methods=['POST'])
@admin_required
def supplier_create():
    data = request.json
    if not data.get('name'):
        return jsonify({'error': 'Naziv je obavezan'}), 400
    conn = get_db()
    conn.execute("INSERT INTO suppliers (name, oib, address) VALUES (?,?,?)",
                 (data['name'].strip(), data.get('oib','').strip(), data.get('address','').strip()))
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'id': new_id})"""

NEW1 = """@app.route('/api/suppliers', methods=['POST'])
@api_login_required
def supplier_create():
    user = get_current_user()
    if not user or not user.get('is_admin'):
        return jsonify({'success': False, 'error': 'Nemate ovlasti za ovu akciju.'}), 403
    data = request.json
    if not data.get('name'):
        return jsonify({'error': 'Naziv je obavezan'}), 400
    conn = get_db()
    conn.execute("INSERT INTO suppliers (name, oib, address) VALUES (?,?,?)",
                 (data['name'].strip(), data.get('oib','').strip(), data.get('address','').strip()))
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'id': new_id})"""

# --- Patch 2: supplier_update (PUT) ---
OLD2 = """@app.route('/api/suppliers/<int:sid>', methods=['PUT'])
@admin_required
def supplier_update(sid):
    data = request.json
    conn = get_db()
    conn.execute("UPDATE suppliers SET name=?, oib=?, address=? WHERE id=?",
                 (data.get('name','').strip(), data.get('oib','').strip(), data.get('address','').strip(), sid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})"""

NEW2 = """@app.route('/api/suppliers/<int:sid>', methods=['PUT'])
@api_login_required
def supplier_update(sid):
    user = get_current_user()
    if not user or not user.get('is_admin'):
        return jsonify({'success': False, 'error': 'Nemate ovlasti za ovu akciju.'}), 403
    data = request.json
    conn = get_db()
    conn.execute("UPDATE suppliers SET name=?, oib=?, address=? WHERE id=?",
                 (data.get('name','').strip(), data.get('oib','').strip(), data.get('address','').strip(), sid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})"""

# --- Patch 3: supplier_delete (DELETE) ---
OLD3 = """@app.route('/api/suppliers/<int:sid>', methods=['DELETE'])
@admin_required
def supplier_delete(sid):
    conn = get_db()
    conn.execute("DELETE FROM suppliers WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})"""

NEW3 = """@app.route('/api/suppliers/<int:sid>', methods=['DELETE'])
@api_login_required
def supplier_delete(sid):
    user = get_current_user()
    if not user or not user.get('is_admin'):
        return jsonify({'success': False, 'error': 'Nemate ovlasti za ovu akciju.'}), 403
    conn = get_db()
    conn.execute("DELETE FROM suppliers WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})"""

patches = [
    ("supplier_create (POST)", OLD1, NEW1),
    ("supplier_update (PUT)",  OLD2, NEW2),
    ("supplier_delete (DELETE)", OLD3, NEW3),
]

ok = True
for label, old, new in patches:
    if old not in src:
        print(f"⚠️  PATCH PRESKOČEN — pattern nije pronađen: {label}")
        ok = False
    else:
        src = src.replace(old, new, 1)
        print(f"✅ Patch primijenjen: {label}")

if ok:
    with open(APP, 'w', encoding='utf-8') as f:
        f.write(src)
    print("\n🎉 app.py uspješno ažuriran!")
    print("   Restart Flask servera pa testiraj dodavanje dobavljača.")
else:
    print("\n❌ Neki patchi nisu primijenjeni — app.py nije mijenjan.")
    print("   Provjeri sadržaj app.py oko linija supplier_create/update/delete.")

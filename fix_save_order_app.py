#!/usr/bin/env python3
"""
fix_save_order_app.py
Ispravlja dva buga u app.py funkciji save_order():
1. NameError: 'expenses' is not defined  (linija ~1677)
2. database is locked (konekcija nije zatvorena pri early return)

Pokreni iz korijena projekta:
    python fix_save_order_app.py
"""

import shutil
from pathlib import Path

APP_PATH = Path("app.py")

if not APP_PATH.exists():
    print(f"❌ Datoteka nije pronađena: {APP_PATH}")
    exit(1)

backup = APP_PATH.with_suffix(".py.bak")
shutil.copy2(APP_PATH, backup)
print(f"✅ Backup: {backup}")

content = APP_PATH.read_text(encoding="utf-8")

# ── FIX: Cijela save_order funkcija — zamijeni s ispravnom verzijom ──────────
# Pronađi blok od dekoratora do kraja funkcije i zamijeni ga.
# Tražimo specifičan potpis koji je jedinstven u kodu.

OLD_BLOCK = '''    # Check if existing order is locked (submitted or approved)
    if order_id:
        existing = conn.execute("SELECT status FROM travel_orders WHERE id=?", (order_id,)).fetchone()
        if existing:
            old_status = existing['status']
            # Only allow status changes from locked states, not data edits
            locked_statuses = ['submitted', 'approved']
            if old_status in locked_statuses:
                # Only allow: approved->rejected, submitted->rejected, submitted->approved
                allowed_transitions = {
                    'submitted': ['approved', 'rejected'],
                    'approved': ['rejected', 'knjizeno'],
                    'knjizeno': ['rejected'],
                }
                if new_status not in allowed_transitions.get(old_status, []):
                    conn.close()
                    return jsonify({'error': f'Cannot edit order with status: {old_status}'}), 403
                # Status-only change - just update status
                conn.execute("UPDATE travel_orders SET status=?, updated_at=? WHERE id=?",
                           (new_status, datetime.now().isoformat(), order_id))
                # If approving - generate and save PDF
                if new_status == 'approved':
                    conn.commit()
                    conn.close()
                    return _generate_and_save_pdf(order_id)
                conn.commit()
                conn.close()
                return jsonify({'success': True, 'id': order_id, 'auto_id': auto_id, 'status': new_status})

    # Calculate dnevnice'''

NEW_BLOCK = '''    # Pročitaj expenses ODMAH — mora biti definirano prije bilo kojeg returna
    expenses = data.get('expenses', [])

    # Check if existing order is locked (submitted or approved)
    if order_id:
        existing = conn.execute("SELECT status FROM travel_orders WHERE id=?", (order_id,)).fetchone()
        if existing:
            old_status = existing['status']
            # Only allow status changes from locked states, not data edits
            locked_statuses = ['submitted', 'approved']
            if old_status in locked_statuses:
                # Only allow: approved->rejected, submitted->rejected, submitted->approved
                allowed_transitions = {
                    'submitted': ['approved', 'rejected'],
                    'approved': ['rejected', 'knjizeno'],
                    'knjizeno': ['rejected'],
                }
                if new_status not in allowed_transitions.get(old_status, []):
                    conn.close()
                    return jsonify({'error': f'Cannot edit order with status: {old_status}'}), 403
                # Status-only change - just update status
                conn.execute("UPDATE travel_orders SET status=?, updated_at=? WHERE id=?",
                           (new_status, datetime.now().isoformat(), order_id))
                # If approving - generate and save PDF
                if new_status == 'approved':
                    conn.commit()
                    conn.close()
                    return _generate_and_save_pdf(order_id)
                conn.commit()
                conn.close()
                return jsonify({'success': True, 'id': order_id, 'auto_id': auto_id, 'status': new_status})

    # Calculate dnevnice'''

if OLD_BLOCK in content:
    content = content.replace(OLD_BLOCK, NEW_BLOCK)
    print("✅ Fix: 'expenses = data.get(...)' premješteno ispred early-return bloka.")
else:
    print("⚠️  Nije pronađen očekivani blok koda. Provjeri ima li app.py već fix ili je kod drugačiji.")
    print()
    print("Ručni fix: u funkciji save_order(), odmah nakon:")
    print("    expenses = data.get('expenses', [])")
    print("premjesti tu liniju IZNAD bloka '# Check if existing order is locked'")
    print()
    # Pokušaj alternativno — samo provjeri je li već fixano
    if "# Pročitaj expenses ODMAH" in content:
        print("ℹ️  Fix je već primijenjen u kodu.")
    APP_PATH.write_text(content, encoding="utf-8")
    exit(0)

# ── Dodatno: ukloni duplicirani 'expenses = data.get(...)' koji ostaje niže ──
# Nakon premještanja, originalna linija ostaje na starom mjestu — treba je ukloniti
OLD_DUP = '''    # Calculate totals
    expenses = data.get('expenses', [])'''

NEW_DUP = '''    # Calculate totals'''

if OLD_DUP in content:
    content = content.replace(OLD_DUP, NEW_DUP)
    print("✅ Uklonjen duplikat 'expenses = data.get(...)' na originalnoj lokaciji.")
else:
    # Možda nema duplikata — OK
    print("ℹ️  Duplikat nije pronađen (sve OK).")

APP_PATH.write_text(content, encoding="utf-8")
print(f"\n✅ Gotovo! Datoteka ažurirana: {APP_PATH}")
print("\nRestart aplikacije:")
print("  Ctrl+C pa python app.py")
print("\nZatim provjeri gumb 'Spremi nacrt' — treba raditi bez grešaka u logu.")

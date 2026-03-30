#!/usr/bin/env python3
"""
Patch: sinkronizacija načina plaćanja iz PN troška u Ulazne račune.

Problem: INSERT u invoices (linija ~6926) ne uključuje is_paid, paid_at,
paid_card_last4 — pa ulazni račun uvijek ostaje "Označi" (neplaćeno).

Pokreni iz korijenskog direktorija projekta:
    python3 patch_pn_expense_payment_sync.py
"""

import shutil, os

TARGET = 'app.py'
BACKUP = TARGET + '.bak'

if not os.path.exists(TARGET):
    print(f"❌ Nije pronađen: {TARGET}")
    exit(1)

shutil.copy2(TARGET, BACKUP)
print(f"✅ Backup: {BACKUP}")

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# ── FIX 1: Dodaj is_paid, paid_at, paid_card_last4 u invoices INSERT ───────

OLD_INVOICE_INSERT = '''    # R1 račun — kreiraj i u invoices tablici
    if doc_type == 'r1':
        c.execute("""
            INSERT INTO invoices (
                invoice_number, partner_name, partner_oib,
                invoice_date, due_date, amount_total, currency,
                original_filename, stored_filename, stored_path,
                ocr_raw, notes, created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,'EUR',?,?,?,?,?,?,?,?)
        """, (
            data.get('invoice_number', ''),
            data.get('partner_name', ''),
            data.get('partner_oib', ''),
            doc_date,
            data.get('due_date', ''),
            float(data.get('amount', 0) or 0),
            data.get('original_filename', ''),
            stored_filename, stored_path,
            data.get('ocr_raw', ''),
            'Uneseno kroz modul Putni nalozi',
            user.get('user_id') if user else None,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        invoice_id = c.lastrowid'''

NEW_INVOICE_INSERT = '''    # R1 račun — kreiraj i u invoices tablici
    if doc_type == 'r1':
        # Odredi podatke o plaćanju
        _payment_method = data.get('payment_method', 'private')
        _bank_card_id = data.get('bank_card_id') or None
        _is_paid = 0 if _payment_method == 'transfer' else 1
        _paid_at = doc_date if _is_paid else None
        _paid_card_last4 = None
        if _payment_method == 'card' and _bank_card_id:
            try:
                _card = conn.execute(
                    "SELECT last4 FROM bank_cards WHERE id=?", (_bank_card_id,)
                ).fetchone()
                if _card:
                    _paid_card_last4 = _card['last4']
            except:
                pass

        c.execute("""
            INSERT INTO invoices (
                invoice_number, partner_name, partner_oib,
                invoice_date, due_date, amount_total, currency,
                original_filename, stored_filename, stored_path,
                ocr_raw, notes, created_by, created_at, updated_at,
                is_paid, paid_at, paid_card_last4
            ) VALUES (?,?,?,?,?,?,'EUR',?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get('invoice_number', ''),
            data.get('partner_name', ''),
            data.get('partner_oib', ''),
            doc_date,
            data.get('due_date', ''),
            float(data.get('amount', 0) or 0),
            data.get('original_filename', ''),
            stored_filename, stored_path,
            data.get('ocr_raw', ''),
            'Uneseno kroz modul Putni nalozi',
            user.get('user_id') if user else None,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            _is_paid, _paid_at, _paid_card_last4
        ))
        invoice_id = c.lastrowid'''

if OLD_INVOICE_INSERT in content:
    content = content.replace(OLD_INVOICE_INSERT, NEW_INVOICE_INSERT, 1)
    print("✅ FIX 1: Dodan is_paid/paid_at/paid_card_last4 u invoices INSERT")
else:
    print("❌ FIX 1: Pattern nije pronađen!")
    exit(1)

# ── FIX 2: Sync u pn_expense_update ────────────────────────────────────────

OLD_UPDATE_END = '''    if updates:
        updates.append("updated_at=?")
        params.append(datetime.now().isoformat())
        params.append(expense_id)
        conn.execute(f"UPDATE pn_expenses SET {', '.join(updates)} WHERE id=?", params)
        conn.commit()
    conn.close()
    audit('update', module='pn_expenses', entity='pn_expense', entity_id=expense_id)
    return jsonify({'success': True})'''

NEW_UPDATE_END = '''    if updates:
        updates.append("updated_at=?")
        params.append(datetime.now().isoformat())
        params.append(expense_id)
        conn.execute(f"UPDATE pn_expenses SET {', '.join(updates)} WHERE id=?", params)

        # Sinkroniziraj plaćanje na vezani invoice ako postoji
        if any(f in data for f in ('payment_method', 'bank_card_id', 'doc_date')):
            try:
                exp_row = conn.execute(
                    "SELECT invoice_id, payment_method, bank_card_id, doc_date, doc_type FROM pn_expenses WHERE id=?",
                    (expense_id,)
                ).fetchone()
                if exp_row and exp_row['invoice_id'] and exp_row['doc_type'] == 'r1':
                    _pm = data.get('payment_method', exp_row['payment_method'] or 'private')
                    _bcid = data.get('bank_card_id', exp_row['bank_card_id'])
                    _dd = data.get('doc_date', exp_row['doc_date'] or '')
                    _is_paid = 0 if _pm == 'transfer' else 1
                    _paid_at = _dd if _is_paid else None
                    _paid_last4 = None
                    if _pm == 'card' and _bcid:
                        _card = conn.execute(
                            "SELECT last4 FROM bank_cards WHERE id=?", (_bcid,)
                        ).fetchone()
                        if _card:
                            _paid_last4 = _card['last4']
                    conn.execute("""
                        UPDATE invoices
                        SET is_paid=?, paid_at=?, paid_card_last4=?, updated_at=?
                        WHERE id=?
                    """, (_is_paid, _paid_at, _paid_last4,
                          datetime.now().isoformat(), exp_row['invoice_id']))
            except:
                pass

        conn.commit()
    conn.close()
    audit('update', module='pn_expenses', entity='pn_expense', entity_id=expense_id)
    return jsonify({'success': True})'''

if OLD_UPDATE_END in content:
    content = content.replace(OLD_UPDATE_END, NEW_UPDATE_END, 1)
    print("✅ FIX 2: Dodan payment sync u pn_expense_update")
else:
    print("⚠️  FIX 2: pn_expense_update pattern nije pronađen — preskoči")

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎉 Patch završen!")
print("   Restartaj Flask i testiraj:")
print("   1. Unesi novi R1 trošak s Visa karticom")
print("   2. Provjeri Ulazne račune → treba biti 'Plaćeno' s last4 kartice")
print("\n   Git commit:")
print("   cd ~/Projects/Softman_app && git add app.py && git commit -m 'fix: is_paid i paid_card_last4 sinkronizirani iz PN troska u Ulazne racune' && git push origin main")

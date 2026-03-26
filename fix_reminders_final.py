#!/usr/bin/env python3
"""
fix_reminders_final.py  —  pokreni: python3 fix_reminders_final.py

Pronalazi /api/loans/check-reminders route u app.py i zamjenjuje ga
ispravnom verzijom koja:
  - koristi payment_date kolonu (kako tablica već postoji)
  - šalje mail kada rata DOSPIJEVA (days_before=0 = na dan dospijeća)
  - preskače PLAĆENE rate (paid=True u schedule_json)
  - uvijek vraća JSON (nikad HTML)
"""
import os, re

ROOT   = os.path.dirname(os.path.abspath(__file__))
APP_PY = os.path.join(ROOT, 'app.py')

OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m~\033[0m"

print("\n══════════════════════════════════════════")
print("  Fix final: check-reminders route")
print("══════════════════════════════════════════\n")

with open(APP_PY, encoding='utf-8') as f:
    src = f.read()

# Pronađi postojeći check-reminders route
start = src.find("@app.route('/api/loans/check-reminders'")
if start == -1:
    start = src.find('@app.route("/api/loans/check-reminders"')

if start == -1:
    print(f"   {FAIL} Route nije pronađen u app.py!")
    exit(1)

# Pronađi kraj route-a
end = src.find('\n@app.route', start + 10)
if end == -1:
    end = src.find('\nif __name__', start + 10)
if end == -1:
    end = len(src)

old_route = src[start:end]
print(f"   Pronađen route (pozicija {start}–{end})")
print(f"   Prvih 200 znakova:\n   {old_route[:200]}\n")

NEW_ROUTE = '''@app.route('/api/loans/check-reminders', methods=['POST'])
@api_login_required
def check_loan_reminders():
    """Pošalji email podsjetnik za rate koje dospijevaju danas (ili za N dana)."""
    try:
        import smtplib, json as _json
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from datetime import timedelta

        conn = get_db()
        s = {r['key']: r['value'] for r in conn.execute("SELECT key, value FROM settings").fetchall()}

        smtp_host     = (s.get('smtp_host') or '').strip()
        smtp_port     = int(s.get('smtp_port') or 587)
        smtp_user     = (s.get('smtp_user') or '').strip()
        smtp_password = (s.get('smtp_password') or '')
        smtp_from     = (s.get('smtp_from') or smtp_user).strip()
        use_tls       = str(s.get('smtp_use_tls', '1')) == '1'
        company       = (s.get('company_name') or 'Softman App').strip()
        days_before   = int(s.get('loan_reminder_days_before') or 0)
        subject_tpl   = (s.get('loan_reminder_subject') or
                         'Podsjetnik: rata pozajmice {loan_name} dospijeva {date}')
        body_tpl      = (s.get('loan_reminder_body') or
                         'Postovani,\\n\\nPodsjecamo Vas da rata pozajmice "{loan_name}" '
                         'u iznosu {amount} EUR dospijeva {date}.\\n\\nLijep pozdrav,\\n{company_name}')

        if not smtp_host or not smtp_user:
            conn.close()
            return jsonify({'success': False, 'results': [],
                            'message': 'SMTP nije konfiguriran. Postavite ga u Postavke → Email / SMTP.'})

        today       = datetime.now().date()
        target_date = (today + timedelta(days=days_before)).isoformat()

        # Dohvati sve pozajmice s email adresama
        all_loans = conn.execute(
            "SELECT * FROM loans WHERE reminder_emails IS NOT NULL AND reminder_emails != ''"
        ).fetchall()

        # Kreiraj loan_reminders tablicu ako ne postoji
        conn.execute("""CREATE TABLE IF NOT EXISTS loan_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL,
            payment_date TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            recipients TEXT,
            UNIQUE(loan_id, payment_date)
        )""")
        conn.commit()

        results = []

        for loan in all_loans:
            loan_d = dict(loan)
            emails = [e.strip() for e in (loan_d.get('reminder_emails') or '').split(',')
                      if e.strip() and '@' in e]
            if not emails:
                continue

            # Parsiraj schedule_json
            schedule = []
            try:
                schedule = _json.loads(loan_d.get('schedule_json') or '[]')
            except:
                pass

            for entry in schedule:
                rate_date = entry.get('date', '')

                # Preskoci ako datum ne odgovara
                if rate_date != target_date:
                    continue

                # Preskoci placene rate
                if entry.get('paid'):
                    continue

                # Provjeri je li reminder vec poslan za ovaj loan + datum
                already = conn.execute(
                    "SELECT id FROM loan_reminders WHERE loan_id=? AND payment_date=?",
                    (loan_d['id'], rate_date)
                ).fetchone()
                if already:
                    results.append({
                        'loan': loan_d['name'], 'date': rate_date,
                        'ok': False, 'msg': 'Reminder vec poslan za ovaj datum'
                    })
                    continue

                # Pripremi i pošalji email
                amount = entry.get('amount', 0)
                subst = {
                    'loan_name':    loan_d['name'],
                    'date':         rate_date,
                    'amount':       f"{float(amount):,.2f}".replace(',', '.'),
                    'company_name': company,
                }
                subject = subject_tpl.format(**subst)
                body    = body_tpl.format(**subst)

                try:
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = subject
                    msg['From']    = smtp_from or smtp_user
                    msg['To']      = ', '.join(emails)
                    msg.attach(MIMEText(body, 'plain', 'utf-8'))

                    html_body = body.replace('\\n', '<br>').replace('\\n', '<br>')
                    msg.attach(MIMEText(
                        f'<html><body style="font-family:Arial,sans-serif;font-size:14px;">'
                        f'<p>{html_body}</p></body></html>',
                        'html', 'utf-8'
                    ))

                    if use_tls:
                        srv = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                        srv.ehlo()
                        srv.starttls()
                    else:
                        srv = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)

                    srv.login(smtp_user, smtp_password)
                    srv.sendmail(smtp_from or smtp_user, emails, msg.as_string())
                    srv.quit()

                    # Logiraj uspješno slanje
                    conn.execute(
                        "INSERT OR IGNORE INTO loan_reminders (loan_id, payment_date, recipients) VALUES (?,?,?)",
                        (loan_d['id'], rate_date, ', '.join(emails))
                    )
                    conn.commit()

                    results.append({
                        'loan': loan_d['name'], 'date': rate_date,
                        'ok':   True,
                        'msg':  f"Poslan na: {', '.join(emails)}"
                    })

                except smtplib.SMTPAuthenticationError:
                    results.append({
                        'loan': loan_d['name'], 'date': rate_date,
                        'ok':   False,
                        'msg':  'SMTP autentifikacija nije uspjela — provjeri lozinku/App Password'
                    })
                except Exception as mail_err:
                    results.append({
                        'loan': loan_d['name'], 'date': rate_date,
                        'ok':   False, 'msg': str(mail_err)
                    })

        conn.close()

        if not results:
            return jsonify({
                'success': True, 'results': [],
                'message': (f'Nema neplacenih rata koje dospijevaju '
                            f'{"danas" if days_before == 0 else f"za {days_before} dan(a)"} '
                            f'({target_date}), ili nema pozajmica s email adresama.')
            })

        ok_count = sum(1 for r in results if r['ok'])
        return jsonify({
            'success': True,
            'results': results,
            'message': f'Poslano {ok_count}/{len(results)} podsjetnika.'
        })

    except Exception as e:
        return jsonify({'success': False, 'results': [], 'message': f'Greška: {str(e)}'})

'''

# Zamijeni stari route novim
new_src = src[:start] + NEW_ROUTE + src[end:]

with open(APP_PY, 'w', encoding='utf-8') as f:
    f.write(new_src)

print(f"   {OK} Route zamijenjen ispravnom verzijom")
print()
print("✅ Gotovo! Restartaj Flask:")
print("   python3 app.py")
print()
print("Logika slanja:")
print("  • mail se šalje kada rata DOSPIJEVA (days_before=0 = danas)")
print("  • plaćene rate (paid=true) se preskačaju")
print("  • isti mail se ne šalje dva puta za isti datum")
print()
print("Push:")
print("  git add . && git commit -m 'Fix: check-reminders — payment_date, skip paid' && git push origin main")
print("══════════════════════════════════════════\n")

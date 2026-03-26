#!/usr/bin/env python3
"""
fix_check_reminders.py  —  pokreni: python fix_check_reminders.py

FIX: SyntaxError Unexpected token '<' na gumbu "Pokreni provjeru odmah"
UZROK: /api/loans/check-reminders route ne postoji ili vraća HTML redirect
RJEŠENJE:
  1. app.py   — dodaj/popravi route s @api_login_required + uvijek vraća JSON
  2. settings.html — triggerReminders() provjeri Content-Type prije .json()
"""
import os, re

ROOT      = os.path.dirname(os.path.abspath(__file__))
APP_PY    = os.path.join(ROOT, 'app.py')
TEMPLATES = os.path.join(ROOT, 'templates')
SETTINGS  = os.path.join(TEMPLATES, 'settings.html')

OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m~\033[0m"

print("\n══════════════════════════════════════════════════════")
print("  Fix: SyntaxError na 'Pokreni provjeru odmah'")
print("══════════════════════════════════════════════════════\n")

# ── 1. app.py — api_login_required helper ─────────────────────────────────────
print("1. app.py — provjera api_login_required helpera")

with open(APP_PY, encoding='utf-8') as f:
    src = f.read()

API_LR = '''
def api_login_required(f):
    """Login required za API rute — vraća JSON 401 umjesto HTML redirecta."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Unauthorized',
                            'message': 'Sesija je istekla. Prijavite se ponovno.'}), 401
        return f(*args, **kwargs)
    return decorated
'''

if 'def api_login_required' not in src:
    idx = src.find('\ndef admin_required')
    end = src.find('\ndef ', idx + 1)
    src = src[:end] + '\n' + API_LR + src[end:]
    print(f"   {OK} api_login_required dodan")
else:
    print(f"   {SKIP} api_login_required već postoji")

# ── 2. app.py — check-reminders route ────────────────────────────────────────
print("\n2. app.py — route /api/loans/check-reminders")

CHECK_ROUTE = '''
@app.route('/api/loans/check-reminders', methods=['POST'])
@api_login_required
def check_loan_reminders():
    """Provjeri sve pozajmice i pošalji email podsjetnika za rate koje dospijevaju."""
    try:
        import smtplib, json as _json
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        conn = get_db()
        s = {r['key']: r['value'] for r in conn.execute("SELECT key, value FROM settings").fetchall()}

        smtp_host     = (s.get('smtp_host') or '').strip()
        smtp_port     = int(s.get('smtp_port') or 587)
        smtp_user     = (s.get('smtp_user') or '').strip()
        smtp_password = (s.get('smtp_password') or '')
        smtp_from     = (s.get('smtp_from') or smtp_user).strip()
        use_tls       = str(s.get('smtp_use_tls', '1')) == '1'
        company       = (s.get('company_name') or 'Softman App').strip()
        days_before   = int(s.get('loan_reminder_days_before') or 3)
        subject_tpl   = s.get('loan_reminder_subject') or 'Podsjetnik: rata pozajmice {loan_name} dospijeva {date}'
        body_tpl      = s.get('loan_reminder_body') or (
            'Poštovani,\\n\\nPodsječamo Vas da rata pozajmice "{loan_name}" '
            'u iznosu {amount} € dospijeva {date}.\\n\\nLijep pozdrav,\\n{company_name}'
        )

        if not smtp_host or not smtp_user:
            conn.close()
            return jsonify({'success': False, 'results': [],
                            'message': 'SMTP nije konfiguriran. Postavite ga u Postavke → Email / SMTP.'})

        today = datetime.now().date()
        from datetime import timedelta
        target_date = (today + timedelta(days=days_before)).isoformat()

        # Dohvati sve pozajmice s email adresama
        loans = conn.execute(
            "SELECT * FROM loans WHERE reminder_emails IS NOT NULL AND reminder_emails != ''"
        ).fetchall() if 'reminder_emails' in [r[1] for r in conn.execute("PRAGMA table_info(loans)").fetchall()] else []

        results = []

        # Kreiraj loan_reminders tablicu ako ne postoji
        conn.execute("""CREATE TABLE IF NOT EXISTS loan_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL,
            reminder_date TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(loan_id, reminder_date)
        )""")
        conn.commit()

        for loan in loans:
            loan_d = dict(loan)
            emails = [e.strip() for e in (loan_d.get('reminder_emails') or '').split(',') if e.strip() and '@' in e]
            if not emails:
                continue

            # Dohvati raspored rata
            schedule = []
            try:
                schedule = _json.loads(loan_d.get('schedule_json') or '[]')
            except:
                pass

            for entry in schedule:
                rate_date = entry.get('date', '')
                if rate_date != target_date:
                    continue
                if entry.get('paid'):
                    continue

                # Provjeri je li reminder već poslan za ovaj loan + datum
                already = conn.execute(
                    "SELECT id FROM loan_reminders WHERE loan_id=? AND reminder_date=?",
                    (loan_d['id'], rate_date)
                ).fetchone()
                if already:
                    results.append({'loan': loan_d['name'], 'date': rate_date,
                                    'ok': False, 'msg': 'Reminder već poslan danas'})
                    continue

                # Pošalji email
                amount = entry.get('amount', 0)
                subst = {
                    'loan_name': loan_d['name'],
                    'date': rate_date,
                    'amount': f"{float(amount):.2f}",
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
                    html_body = body.replace('\\n', '<br>')
                    msg.attach(MIMEText(f'<html><body><p>{html_body}</p></body></html>', 'html', 'utf-8'))

                    if use_tls:
                        srv = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                        srv.ehlo(); srv.starttls()
                    else:
                        srv = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
                    srv.login(smtp_user, smtp_password)
                    srv.sendmail(smtp_from or smtp_user, emails, msg.as_string())
                    srv.quit()

                    # Logiraj slanje
                    conn.execute(
                        "INSERT OR IGNORE INTO loan_reminders (loan_id, reminder_date) VALUES (?,?)",
                        (loan_d['id'], rate_date)
                    )
                    conn.commit()
                    results.append({'loan': loan_d['name'], 'date': rate_date,
                                    'ok': True, 'msg': f"Poslan na: {', '.join(emails)}"})
                except Exception as mail_err:
                    results.append({'loan': loan_d['name'], 'date': rate_date,
                                    'ok': False, 'msg': str(mail_err)})

        conn.close()

        if not results:
            return jsonify({'success': True, 'results': [],
                            'message': f'Nema rata koje dospijevaju za {days_before} dan(a) ili nema pozajmica s email adresama.'})

        return jsonify({'success': True, 'results': results})

    except Exception as e:
        return jsonify({'success': False, 'results': [], 'message': f'Greška: {str(e)}'})

'''

# Pronađi postoji li route već
existing_idx = src.find("@app.route('/api/loans/check-reminders'")
if existing_idx == -1:
    existing_idx = src.find('@app.route("/api/loans/check-reminders"')

if existing_idx != -1:
    # Route postoji — zamijeni ga
    next_r = src.find('\n@app.route', existing_idx + 10)
    if next_r == -1:
        next_r = src.find('\nif __name__', existing_idx + 10)
    if next_r == -1:
        next_r = len(src)
    old_route = src[existing_idx:next_r]
    if '@api_login_required' in old_route and 'jsonify' in old_route:
        print(f"   {SKIP} Route već ima api_login_required i jsonify — OK")
    else:
        src = src[:existing_idx] + CHECK_ROUTE.strip() + '\n' + src[next_r:]
        print(f"   {OK} Postojeći route zamijenjen robustnom verzijom")
else:
    # Route ne postoji — dodaj ispred if __name__ ili na kraj
    ins = src.rfind('\nif __name__')
    if ins == -1:
        src += '\n' + CHECK_ROUTE
        print(f"   {OK} Route dodan na kraj app.py")
    else:
        src = src[:ins] + '\n' + CHECK_ROUTE + src[ins:]
        print(f"   {OK} Route dodan u app.py")

with open(APP_PY, 'w', encoding='utf-8') as f:
    f.write(src)

# ── 3. settings.html — triggerReminders() ────────────────────────────────────
print("\n3. settings.html — robustni triggerReminders()")

with open(SETTINGS, encoding='utf-8') as f:
    html = f.read()

OLD_TRIGGER = """function triggerReminders() {
  const el = document.getElementById('emailResult');
  el.innerHTML = '<span style="color:var(--gray-500);">⏳ Pokretanje provjere svih pozajmica...</span>';
  fetch('/api/loans/check-reminders', {method: 'POST'})
  .then(r => r.json())
  .then(d => {
    if (!d.results || d.results.length === 0) { el.innerHTML = '<span style="color:var(--gray-500);">ℹ️ Nema rata za slanje danas (ili nema pozajmica s email adresama).</span>'; return; }
    el.innerHTML = d.results.map(r => `${r.ok?'✅':'❌'} <strong>${r.loan}</strong> (${r.date}): ${r.msg}`).join('<br>');
    toast(`Provjera završena: ${d.results.length} rata obrađeno`, 'success');
  })
  .catch(e => { el.innerHTML = `<span style="color:var(--red);">❌ ${e}</span>`; });
}"""

NEW_TRIGGER = """function triggerReminders() {
  const el = document.getElementById('emailResult');
  el.innerHTML = '<span style="color:var(--gray-500);">⏳ Pokretanje provjere svih pozajmica...</span>';
  fetch('/api/loans/check-reminders', {method: 'POST'})
  .then(async r => {
    const ct = r.headers.get('content-type') || '';
    if (!ct.includes('application/json')) {
      el.innerHTML = r.status === 401
        ? '<span style="color:var(--red);">❌ Sesija istekla. Osvježi stranicu i prijavi se.</span>'
        : `<span style="color:var(--red);">❌ Greška servera (HTTP ${r.status}). Provjeri logs.</span>`;
      toast('Greška servera', 'error'); return;
    }
    const d = await r.json();
    if (d.message && (!d.results || d.results.length === 0)) {
      el.innerHTML = `<span style="color:var(--gray-500);">ℹ️ ${d.message}</span>`;
      return;
    }
    if (!d.results || d.results.length === 0) {
      el.innerHTML = '<span style="color:var(--gray-500);">ℹ️ Nema rata za slanje danas (ili nema pozajmica s email adresama).</span>';
      return;
    }
    el.innerHTML = d.results.map(r => `${r.ok?'✅':'❌'} <strong>${r.loan}</strong> (${r.date}): ${r.msg}`).join('<br>');
    toast(`Provjera završena: ${d.results.length} rata obrađeno`, 'success');
  })
  .catch(e => { el.innerHTML = `<span style="color:var(--red);">❌ Mrežna greška: ${e.message||e}</span>`; });
}"""

if 'async r =>' in html and 'check-reminders' in html:
    print(f"   {SKIP} triggerReminders() već ima robustni fetch")
elif OLD_TRIGGER in html:
    html = html.replace(OLD_TRIGGER, NEW_TRIGGER, 1)
    with open(SETTINGS, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"   {OK} triggerReminders() zamijenjen robustnom verzijom")
else:
    # Fallback — zamijeni samo kritični .then(r => r.json()) u triggerReminders
    old_chain = """.then(r => r.json())
  .then(d => {
    if (!d.results || d.results.length === 0) { el.innerHTML = '<span style="color:var(--gray-500);">ℹ️ Nema rata za slanje danas (ili nema pozajmica s email adresama).</span>'; return; }
    el.innerHTML = d.results.map(r => `${r.ok?'✅':'❌'} <strong>${r.loan}</strong> (${r.date}): ${r.msg}`).join('<br>');
    toast(`Provjera završena: ${d.results.length} rata obrađeno`, 'success');
  })
  .catch(e => { el.innerHTML = `<span style="color:var(--red);">❌ ${e}</span>`; });"""

    new_chain = """.then(async r => {
    const ct = r.headers.get('content-type') || '';
    if (!ct.includes('application/json')) {
      el.innerHTML = r.status === 401
        ? '<span style="color:var(--red);">❌ Sesija istekla. Osvježi stranicu i prijavi se.</span>'
        : `<span style="color:var(--red);">❌ Greška servera (HTTP ${r.status}).</span>`;
      toast('Greška servera', 'error'); return;
    }
    const d = await r.json();
    if (!d.results || d.results.length === 0) {
      el.innerHTML = `<span style="color:var(--gray-500);">ℹ️ ${d.message||'Nema rata za slanje danas.'}</span>`;
      return;
    }
    el.innerHTML = d.results.map(r => `${r.ok?'✅':'❌'} <strong>${r.loan}</strong> (${r.date}): ${r.msg}`).join('<br>');
    toast(`Provjera završena: ${d.results.length} rata obrađeno`, 'success');
  })
  .catch(e => { el.innerHTML = `<span style="color:var(--red);">❌ Mrežna greška: ${e.message||e}</span>`; });"""

    if old_chain in html:
        html = html.replace(old_chain, new_chain, 1)
        with open(SETTINGS, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"   {OK} fetch chain zakrpan (fallback)")
    else:
        print(f"   {SKIP} Pattern nije pronađen u settings.html — provjeri ručno")

print()
print("✅ Gotovo! Restartaj Flask:")
print("   python app.py")
print()
print("Push:")
print("   git add . && git commit -m 'Fix: check-reminders JSON route + robustni fetch' && git push origin main")
print("══════════════════════════════════════════════════════\n")

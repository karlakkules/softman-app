#!/usr/bin/env python3
"""
patch_email_fix.py
Pokreni iz root foldera projekta: python patch_email_fix.py

FIX: SyntaxError: Unexpected token '<' pri kliku "Pošalji test mail"
UZROK: Flask route za test-email vraća HTML redirect (login stranicu)
       umjesto JSON-a kada dođe do greške auth/route/iznimke.
       JS fetch tada pokuša parsirati HTML kao JSON → crash.
RJEŠENJE:
  1. app.py   — route /api/loans/test-email: dodaj @login_required koji vraća
                 JSON 401 (ne redirect) + try/except koji uvijek vraća JSON
  2. settings.html — sendTestEmail(): provjeri HTTP status prije .json()
                     i prikaži smislenu poruku za 401/403/500
"""

import os, re, sys

ROOT      = os.path.dirname(os.path.abspath(__file__))
APP_PY    = os.path.join(ROOT, 'app.py')
TEMPLATES = os.path.join(ROOT, 'templates')
SETTINGS  = os.path.join(TEMPLATES, 'settings.html')

OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m~\033[0m"

errors = []

def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def check(path, label):
    if not os.path.exists(path):
        print(f"  {FAIL} {label} — FAJL NIJE PRONAĐEN: {path}")
        errors.append(f"{label}: ne postoji")
        return False
    return True

print("\n╔══════════════════════════════════════════════════════╗")
print("║   Softman — Fix: SyntaxError 'Unexpected token <'   ║")
print("╚══════════════════════════════════════════════════════╝\n")

# ─────────────────────────────────────────────────────────────────────────────
# IZMJENA 1 — app.py: route /api/loans/test-email
#
# Problem: dekorator @login_required (ili @admin_required) radi redirect('/login')
#          za neautorizirani poziv — ali API route mora vratiti JSON, ne HTML.
#
# Fix A: ako route već postoji — zamijeni dekorator s api_login_required
#        koji vraća jsonify({'error': 'Unauthorized'}, 401) umjesto redirecta.
# Fix B: dodaj robustni try/except unutar route funkcije koji uvijek vraća JSON.
# ─────────────────────────────────────────────────────────────────────────────

print("1. app.py — fix route /api/loans/test-email")

if check(APP_PY, 'app.py'):
    app_content = read(APP_PY)

    # ── Korak A: Dodaj helper funkciju api_login_required ako ne postoji ──
    API_LOGIN_REQUIRED = '''
def api_login_required(f):
    """Login required za API rute — vraća JSON 401 umjesto HTML redirecta."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'Sesija je istekla. Prijavite se ponovno.'}), 401
        return f(*args, **kwargs)
    return decorated
'''

    if 'def api_login_required' not in app_content:
        # Ubaci odmah iza def admin_required
        insert_after = 'def admin_required(f):'
        idx = app_content.find(insert_after)
        if idx != -1:
            # Nađi kraj te funkcije (sljedeći def na razini 0)
            end_idx = app_content.find('\ndef ', idx + 1)
            if end_idx == -1:
                end_idx = len(app_content)
            app_content = app_content[:end_idx] + '\n' + API_LOGIN_REQUIRED + app_content[end_idx:]
            print(f"  {OK} app.py — dodana funkcija api_login_required()")
        else:
            print(f"  {SKIP} app.py — nije pronađen insert point za api_login_required (dodaj ručno)")
    else:
        print(f"  {SKIP} app.py — api_login_required već postoji")

    # ── Korak B: Pronađi i popravi route test-email ──
    # Traži postojeći route (može biti anotiran s @login_required ili @admin_required)
    route_pattern = re.compile(
        r"(@app\.route\('/api/loans/test-email'.*?\n)"   # dekorator route
        r"(@(?:login|admin)_required\n)?"               # opcionalni auth dekorator
        r"(def \w+\(\):.*?(?=\n@app\.route|\nif __name__|$))",
        re.DOTALL
    )

    FIXED_ROUTE = '''@app.route('/api/loans/test-email', methods=['POST'])
@api_login_required
def test_email_send():
    """Šalje test email koristeći SMTP postavke iz settings tablice."""
    try:
        data = request.json or {}
        test_to = (data.get('test_to') or '').strip()
        if not test_to or '@' not in test_to:
            return jsonify({'success': False, 'message': 'Nevažeća email adresa.'})

        conn = get_db()
        s = {row['key']: row['value'] for row in conn.execute("SELECT key, value FROM settings").fetchall()}
        conn.close()

        smtp_host     = (s.get('smtp_host') or '').strip()
        smtp_port     = int(s.get('smtp_port') or 587)
        smtp_user     = (s.get('smtp_user') or '').strip()
        smtp_password = (s.get('smtp_password') or '')
        smtp_from     = (s.get('smtp_from') or smtp_user).strip()
        use_tls       = str(s.get('smtp_use_tls', '1')) == '1'
        company       = (s.get('company_name') or 'Softman App').strip()

        if not smtp_host or not smtp_user:
            return jsonify({'success': False, 'message': 'SMTP host i korisničko ime nisu konfigurirani.'})

        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Test email — {company}'
        msg['From']    = smtp_from or smtp_user
        msg['To']      = test_to

        html_body = f"""<html><body>
<p>Ovo je <strong>test email</strong> poslan iz aplikacije <strong>{company}</strong>.</p>
<p>SMTP konfiguracija radi ispravno! ✅</p>
<hr>
<p style="color:#888;font-size:12px;">Softman App · {smtp_host}:{smtp_port}</p>
</body></html>"""

        msg.attach(MIMEText('Test email - SMTP konfiguracija radi ispravno!', 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        if use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)

        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_from or smtp_user, [test_to], msg.as_string())
        server.quit()

        return jsonify({'success': True, 'message': f'Email poslan na {test_to}'})

    except smtplib.SMTPAuthenticationError:
        return jsonify({'success': False, 'message': 'SMTP autentifikacija nije uspjela. Provjeri korisničko ime i lozinku / App Password.'})
    except smtplib.SMTPConnectError as e:
        return jsonify({'success': False, 'message': f'Ne mogu se spojiti na SMTP server: {e}'})
    except smtplib.SMTPRecipientsRefused:
        return jsonify({'success': False, 'message': f'Server je odbio primatelja: {test_to}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Greška: {str(e)}'})

'''

    match = route_pattern.search(app_content)
    if match:
        app_content = app_content[:match.start()] + FIXED_ROUTE + app_content[match.end():]
        print(f"  {OK} app.py — route /api/loans/test-email zamijenjen s robustnom verzijom")
    else:
        # Route ne postoji uopće — dodaj ga ispred if __name__ == '__main__'
        insert_marker = "\nif __name__ == '__main__':"
        idx = app_content.rfind(insert_marker)
        if idx != -1:
            app_content = app_content[:idx] + '\n' + FIXED_ROUTE + app_content[idx:]
            print(f"  {OK} app.py — route /api/loans/test-email DODAN (nije postojao)")
        else:
            # Dodaj na kraj
            app_content += '\n' + FIXED_ROUTE
            print(f"  {OK} app.py — route /api/loans/test-email dodan na kraj fajla")

    write(APP_PY, app_content)


# ─────────────────────────────────────────────────────────────────────────────
# IZMJENA 2 — settings.html: sendTestEmail() — robustna provjera odgovora
#
# Problem: .then(r => r.json()) pada ako server vrati HTML (401 redirect itd.)
# Fix:     provjeri r.ok i content-type prije .json(), prikaži smislenu poruku
# ─────────────────────────────────────────────────────────────────────────────

print("\n2. settings.html — fix sendTestEmail() fetch handler")

if check(SETTINGS, 'settings.html'):
    html = read(SETTINGS)

    OLD_SEND = """function sendTestEmail() {
  const addr = document.getElementById('testEmailAddr').value.trim();
  if (!addr || !addr.includes('@')) { toast('Unesite ispravnu email adresu za test', 'error'); return; }
  const el = document.getElementById('emailResult');
  el.innerHTML = '<span style="color:var(--gray-500);">⏳ Slanje test emaila...</span>';
  fetch('/api/loans/test-email', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({test_to: addr}) })
  .then(r => r.json())
  .then(d => {
    if (d.success) { el.innerHTML = `<span style="color:var(--green);">✅ Test email poslan! ${d.message||''}</span>`; toast('Test email poslan!', 'success'); }
    else { el.innerHTML = `<span style="color:var(--red);">❌ Greška: ${d.message||d.error||'Nepoznata greška'}</span>`; toast('Slanje nije uspjelo — provjeri SMTP postavke', 'error'); }
  })
  .catch(e => { el.innerHTML = `<span style="color:var(--red);">❌ ${e}</span>`; });
}"""

    NEW_SEND = """function sendTestEmail() {
  const addr = document.getElementById('testEmailAddr').value.trim();
  if (!addr || !addr.includes('@')) { toast('Unesite ispravnu email adresu za test', 'error'); return; }
  const el = document.getElementById('emailResult');
  el.innerHTML = '<span style="color:var(--gray-500);">⏳ Slanje test emaila...</span>';
  fetch('/api/loans/test-email', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({test_to: addr}) })
  .then(async r => {
    // Provjeri content-type — ako nije JSON (npr. server vrati HTML redirect), prikaži jasnu grešku
    const ct = r.headers.get('content-type') || '';
    if (!ct.includes('application/json')) {
      if (r.status === 401 || r.status === 403) {
        el.innerHTML = '<span style="color:var(--red);">❌ Sesija je istekla. Osvježi stranicu i prijavi se ponovno.</span>';
        toast('Sesija istekla — prijavi se ponovno', 'error');
      } else {
        el.innerHTML = `<span style="color:var(--red);">❌ Neočekivan odgovor servera (HTTP ${r.status}). Provjeri logs.</span>`;
        toast('Greška servera — provjeri logs', 'error');
      }
      return;
    }
    const d = await r.json();
    if (d.success) {
      el.innerHTML = `<span style="color:var(--green);">✅ Test email poslan! ${d.message||''}</span>`;
      toast('Test email poslan!', 'success');
    } else {
      el.innerHTML = `<span style="color:var(--red);">❌ Greška: ${d.message||d.error||'Nepoznata greška'}</span>`;
      toast('Slanje nije uspjelo — provjeri SMTP postavke', 'error');
    }
  })
  .catch(e => {
    el.innerHTML = `<span style="color:var(--red);">❌ Mrežna greška: ${e.message||e}</span>`;
    toast('Mrežna greška pri slanju', 'error');
  });
}"""

    if OLD_SEND in html:
        html = html.replace(OLD_SEND, NEW_SEND, 1)
        write(SETTINGS, html)
        print(f"  {OK} settings.html — sendTestEmail() zamijenjen robustnom verzijom")
    elif 'async r =>' in html:
        print(f"  {SKIP} settings.html — fix već primijenjen")
    else:
        # Fallback: zamijeni samo .then(r => r.json()) pattern
        fallback_old = ".then(r => r.json())\n  .then(d => {\n    if (d.success) { el.innerHTML = `<span style=\"color:var(--green);\">✅ Test email poslan! ${d.message||''}</span>`; toast('Test email poslan!', 'success'); }\n    else { el.innerHTML = `<span style=\"color:var(--red);\">❌ Greška: ${d.message||d.error||'Nepoznata greška'}</span>`; toast('Slanje nije uspjelo — provjeri SMTP postavke', 'error'); }\n  })\n  .catch(e => { el.innerHTML = `<span style=\"color:var(--red);\">❌ ${e}</span>`; });"
        if fallback_old in html:
            NEW_CHAIN = """.then(async r => {
    const ct = r.headers.get('content-type') || '';
    if (!ct.includes('application/json')) {
      el.innerHTML = r.status === 401
        ? '<span style="color:var(--red);">❌ Sesija istekla. Osvježi stranicu i prijavi se.</span>'
        : `<span style="color:var(--red);">❌ Greška servera (HTTP ${r.status}).</span>`;
      toast('Greška servera', 'error'); return;
    }
    const d = await r.json();
    if (d.success) { el.innerHTML = `<span style="color:var(--green);">✅ Test email poslan! ${d.message||''}</span>`; toast('Test email poslan!', 'success'); }
    else { el.innerHTML = `<span style="color:var(--red);">❌ Greška: ${d.message||d.error||'Nepoznata greška'}</span>`; toast('Slanje nije uspjelo — provjeri SMTP postavke', 'error'); }
  })
  .catch(e => { el.innerHTML = `<span style="color:var(--red);">❌ Mrežna greška: ${e.message||e}</span>`; });"""
            html = html.replace(fallback_old, NEW_CHAIN, 1)
            write(SETTINGS, html)
            print(f"  {OK} settings.html — fetch chain zakrpan (fallback)")
        else:
            print(f"  {SKIP} settings.html — nije pronađen poznati pattern. Provjeri ručno.")
            errors.append("settings.html: sendTestEmail pattern nije pronađen — provjeri ručno")


# ─────────────────────────────────────────────────────────────────────────────
# SAŽETAK
# ─────────────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"⚠️  Završeno s {len(errors)} upozorenjima:")
    for e in errors:
        print(f"   • {e}")
else:
    print("✅ Sve izmjene uspješno primijenjene!")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("Što je promijenjeno:")
print("  app.py      — novi route /api/loans/test-email koji:")
print("                • koristi @api_login_required (vraća JSON 401, ne HTML)")
print("                • šalje pravi SMTP email s try/except")
print("                • uvijek vraća JSON, nikad HTML")
print("  settings.html — sendTestEmail() fetch:")
print("                • provjerava Content-Type prije JSON parsiranja")
print("                • prikazuje jasnu poruku za 401/403/500")
print()
print("Pokrenuti i testirati:")
print("  python app.py")
print()
print("Pushati na GitHub:")
print("  git add . && git commit -m 'Fix: SyntaxError test-email — JSON API + robustni fetch' && git push origin main")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

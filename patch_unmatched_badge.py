#!/usr/bin/env python3
"""
Fix: Neupareni troškovi badge se automatski ažurira nakon link/delete.
Pokreni: python3 patch_unmatched_badge.py
"""
import os, sys, shutil

PATH = os.path.join('templates', 'orders.html')
if not os.path.exists(PATH):
    print(f"❌ {PATH} nije pronađen!"); sys.exit(1)

with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

if 'updateUnmatchedBadge' in content:
    print("⚠️  Badge fix već primijenjen — preskačem.")
    sys.exit(0)

# 1. Dodaj funkciju updateUnmatchedBadge i patchaj linkUnmatched/deleteUnmatched

OLD_LINK = """async function linkUnmatched(expId) {
  const pnId = document.getElementById(`unmatched-pn-${expId}`).value;
  if (!pnId) { toast('Odaberi putni nalog!', 'error'); return; }

  const res = await fetch(`/api/pn-expenses/${expId}/link`, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ travel_order_id: parseInt(pnId) })
  });
  const d = await res.json();
  if (d.success) {
    toast('Trošak vezan na PN!', 'success');
    const row = document.getElementById(`unmatched-row-${expId}`);
    if (row) row.style.display = 'none';
    // Provjeri ima li još neuparenih
    const remaining = document.querySelectorAll('.unmatched-row:not([style*="none"])').length;
    if (!remaining) {
      document.getElementById('unmatched-list').innerHTML =
        '<div style="text-align:center;padding:30px;color:var(--gray-400);"><div style="font-size:28px;margin-bottom:8px;">✅</div>Svi troškovi su upareni!</div>';
    }
  } else { toast(d.error || 'Greška', 'error'); }
}

async function deleteUnmatched(expId) {
  if (!confirm('Obrisati ovaj trošak?')) return;
  const res = await fetch(`/api/pn-expenses/${expId}`, { method: 'DELETE' });
  if (res.ok) {
    toast('Trošak obrisan.', 'success');
    const row = document.getElementById(`unmatched-row-${expId}`);
    if (row) row.style.display = 'none';
  } else { toast('Greška pri brisanju', 'error'); }
}"""

NEW_LINK = """function updateUnmatchedBadge() {
  // Ažuriraj badge broj na gumbu Neupareni troškovi
  const remaining = document.querySelectorAll('.unmatched-row:not([style*="none"])').length;
  const badges = document.querySelectorAll('[onclick="openUnmatched()"] span[style*="position:absolute"]');
  badges.forEach(badge => {
    if (remaining > 0) {
      badge.textContent = remaining;
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }
  });
}

async function linkUnmatched(expId) {
  const pnId = document.getElementById(`unmatched-pn-${expId}`).value;
  if (!pnId) { toast('Odaberi putni nalog!', 'error'); return; }

  const res = await fetch(`/api/pn-expenses/${expId}/link`, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ travel_order_id: parseInt(pnId) })
  });
  const d = await res.json();
  if (d.success) {
    toast('Trošak vezan na PN!', 'success');
    const row = document.getElementById(`unmatched-row-${expId}`);
    if (row) row.style.display = 'none';
    updateUnmatchedBadge();
    const remaining = document.querySelectorAll('.unmatched-row:not([style*="none"])').length;
    if (!remaining) {
      document.getElementById('unmatched-list').innerHTML =
        '<div style="text-align:center;padding:30px;color:var(--gray-400);"><div style="font-size:28px;margin-bottom:8px;">✅</div>Svi troškovi su upareni!</div>';
    }
  } else { toast(d.error || 'Greška', 'error'); }
}

async function deleteUnmatched(expId) {
  if (!confirm('Obrisati ovaj trošak?')) return;
  const res = await fetch(`/api/pn-expenses/${expId}`, { method: 'DELETE' });
  if (res.ok) {
    toast('Trošak obrisan.', 'success');
    const row = document.getElementById(`unmatched-row-${expId}`);
    if (row) row.style.display = 'none';
    updateUnmatchedBadge();
  } else { toast('Greška pri brisanju', 'error'); }
}"""

if OLD_LINK in content:
    content = content.replace(OLD_LINK, NEW_LINK, 1)
    print("✅ linkUnmatched i deleteUnmatched patchani s updateUnmatchedBadge()")
else:
    print("⚠️  Marker za linkUnmatched nije pronađen — ručno provjeri")

shutil.copy2(PATH, PATH + '.bak3')
with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎉 Badge fix primijenjen!")
print("   Gumb 'Neupareni troškovi' sad automatski smanjuje broj kad se troškovi vežu ili obrišu.")
print("   Kad dođe na 0, badge se potpuno sakriva.")

#!/usr/bin/env python3
"""
Patch: vehicle_log_form.html
Bug: DOMContentLoaded rekonstrukcija _csvData ne čuva start_km/end_km po danu iz baze.
     saveLog() ih onda ne šalje, pa app.py prima end_km = start_km za svaki dan.
Fix: 1. Rekonstrukcija čuva start_km i end_km iz baze u breakdown objektu
     2. saveLog() koristi d.start_km i d.end_km iz baze kad postoje (ne računa iz forme)
"""
import shutil
from pathlib import Path

T = Path('templates/vehicle_log_form.html')
if not T.exists():
    print('ERROR: templates/vehicle_log_form.html nije pronađen!'); exit(1)

shutil.copy(T, T.with_suffix('.html.bak'))
c = T.read_text(encoding='utf-8')

# Fix 1: rekonstrukcija _csvData — dodaj start_km i end_km iz baze
OLD_BREAKDOWN = """    // Rekonstruiraj _csvData iz baze
    const breakdown = days.map(function(d) {
      return {
        date: d.date,
        km: (d.total_km || 0),
        pn_km: (d.official_km || 0),
        private_km: (d.private_km || 0),
        is_pn: d.is_pn === 1 && (d.private_km || 0) === 0,
        is_mixed: d.is_pn === 1 && (d.private_km || 0) > 0,
        trips: d.trips || [],
      };
    });"""

NEW_BREAKDOWN = """    // Rekonstruiraj _csvData iz baze
    const breakdown = days.map(function(d) {
      return {
        date: d.date,
        km: (d.total_km || 0),
        pn_km: (d.official_km || 0),
        private_km: (d.private_km || 0),
        is_pn: d.is_pn === 1 && (d.private_km || 0) === 0,
        is_mixed: d.is_pn === 1 && (d.private_km || 0) > 0,
        trips: d.trips || [],
        start_km: (d.start_km || 0),
        end_km: (d.end_km || 0),
      };
    });"""

if OLD_BREAKDOWN in c:
    c = c.replace(OLD_BREAKDOWN, NEW_BREAKDOWN)
    print('✅ Fix 1: breakdown čuva start_km/end_km iz baze')
else:
    print('❌ Fix 1: pattern nije pronađen'); exit(1)

# Fix 2: saveLog() — koristi start_km/end_km iz baze ako postoje
OLD_SAVELOG = """    daily_days = _csvData.daily_breakdown.map(d => {
      const start_km_d = cur_km;
      const total_d = parseFloat(d.km) || 0;
      const end_km_d = Math.round((cur_km + total_d) * 100) / 100;
      cur_km = end_km_d;
      const pn_km = parseFloat(d.pn_km) || 0;
      const priv_km = parseFloat(d.private_km) || 0;
      const comment = pn_km > 0 && priv_km > 0 ? `PN+privatno` :
                      pn_km > 0 ? 'PN' : total_d > 0 ? 'privatno' : '';
      return {
        date: d.date,
        start_km: start_km_d,
        end_km: end_km_d,"""

NEW_SAVELOG = """    daily_days = _csvData.daily_breakdown.map(d => {
      const total_d = parseFloat(d.km) || 0;
      // Koristi stvarne GPS km iz baze ako postoje, inače izračunaj iz forme
      const start_km_d = (d.start_km && d.start_km > 0) ? d.start_km : cur_km;
      const end_km_d = (d.end_km && d.end_km > 0) ? d.end_km : Math.round((cur_km + total_d) * 100) / 100;
      cur_km = end_km_d;
      const pn_km = parseFloat(d.pn_km) || 0;
      const priv_km = parseFloat(d.private_km) || 0;
      const comment = pn_km > 0 && priv_km > 0 ? `PN+privatno` :
                      pn_km > 0 ? 'PN' : total_d > 0 ? 'privatno' : '';
      return {
        date: d.date,
        start_km: start_km_d,
        end_km: end_km_d,"""

if OLD_SAVELOG in c:
    c = c.replace(OLD_SAVELOG, NEW_SAVELOG)
    print('✅ Fix 2: saveLog() koristi GPS km iz baze')
else:
    print('❌ Fix 2: pattern nije pronađen'); exit(1)

T.write_text(c, encoding='utf-8')
print('\n✅ Patch primijenjen!')
print('Testiraj: otvori evidenciju za ožujak, klikni Spremi, pa generiraj PDF.')
print('Početne i završne km trebaju odgovarati GPS podacima.')

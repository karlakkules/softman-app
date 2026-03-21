import sqlite3
from datetime import datetime

DB = 'putni_nalog.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

KARLA = 1
KRESIMIR = 2
VEHICLE = 1
NOW = datetime.now().isoformat()

def fmt_dt(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str.strip()} {time_str.strip()}", '%d/%m/%Y %H:%M').strftime('%Y-%m-%dT%H:%M')
    except:
        return None

def insert_order(auto_id, issue_date, employee_id, approved_by_id, purpose, client,
                 departure_date, expected_duration, start_km, end_km,
                 trip_start, trip_end, trip_days, trip_hours, trip_minutes,
                 dnevnice, rate, daily_total, total_expenses, total_amount,
                 report_text, place_report, expenses_list):
    fields = {
        'auto_id': auto_id, 'status': 'approved', 'issue_date': issue_date,
        'employee_id': employee_id, 'destination': 'Zagreb', 'purpose': purpose,
        'client_info': client, 'expected_duration': expected_duration,
        'departure_date': departure_date, 'vehicle_id': VEHICLE,
        'start_km': start_km, 'end_km': end_km,
        'trip_start_datetime': trip_start, 'trip_end_datetime': trip_end,
        'trip_duration_days': trip_days, 'trip_duration_hours': trip_hours,
        'trip_duration_minutes': trip_minutes,
        'daily_allowance_count': dnevnice, 'daily_allowance_rate': rate,
        'daily_allowance_total': daily_total, 'advance_payment': 0.0,
        'total_expenses': total_expenses, 'total_amount': total_amount,
        'payout_amount': total_amount, 'report_text': report_text,
        'place_of_report': place_report, 'approved_by_id': approved_by_id,
        'validator_id': None, 'cost_center_id': None,
        'is_deleted': 0, 'is_paid': 1, 'paid_at': issue_date,
        'created_at': NOW, 'updated_at': NOW,
    }
    cols = ', '.join(fields.keys())
    placeholders = ', '.join('?' for _ in fields)
    c.execute(f"INSERT INTO travel_orders ({cols}) VALUES ({placeholders})", list(fields.values()))
    order_id = c.lastrowid
    for i, (desc, privately, amount) in enumerate(expenses_list):
        c.execute('''INSERT INTO expenses (travel_order_id, category_id, description, paid_privately, amount, sort_order)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (order_id, None, desc, 1 if privately else 0, amount if privately else 0, i))
    return order_id

insert_order('2026-1','2026-01-09',KRESIMIR,KRESIMIR,'Sastanak s Meddox timom','Meddox Digital d.o.o.','2026-01-09',1,44271,44807,fmt_dt('09/01/2026','07:20'),fmt_dt('09/01/2026','17:55'),0,10,35,0.5,30.0,15.0,34.40,49.40,'Prisustvovanje skupštini društva Meddox Digital.','Zagreb',[('Gorivo (plaćeno poslovnom karticom)',False,0),('Čepin – Zagreb (cestarina)',True,17.20),('Zagreb – Čepin (cestarina)',True,17.20)])
insert_order('2026-2','2026-01-14',KARLA,KARLA,'Sastanak s klijentima – AMG','Arsano Medical Group d.o.o.','2026-01-14',2,44887,45493,fmt_dt('14/01/2025','05:35'),fmt_dt('15/01/2025','18:55'),1,13,20,2.0,30.0,60.0,45.70,105.70,'14.01. sastanak u Avivi vezano za projektne aktivnosti fiskalizacije 2.0 i eRačuna pri HZZO-u.\n15.01. sastanak u AMG grupi – koordinacija aktivnosti.\nPri povratku promašen izlaz Osijek s autoputa.','Zagreb',[('Cestarina Osijek-Zagreb',True,17.70),('Gorivo 1 (plaćeno službenom karticom)',False,0),('Cestarina Zagreb-Velika Kopanica',True,14.70),('Cestarina Velika Kopanica-Osijek',True,4.20),('Gorivo 2 (plaćeno službenom karticom)',False,0),('Gorivo 3 (plaćeno službenom karticom)',False,0),('Parking 1',True,0.70),('Parking 2',True,0.70),('Parking 3',True,3.20),('Parking 4',True,3.20),('Parking 5',True,1.30)])
insert_order('2026-3','2026-01-19',KRESIMIR,KRESIMIR,'Sastanak s Meddox timom','Meddox Digital d.o.o.','2026-01-19',1,45559,46111,fmt_dt('19/01/2026','08:05'),fmt_dt('19/01/2026','21:00'),0,12,55,1.0,30.0,30.0,44.60,74.60,'Okupljanje cijelog Meddox tima na radnom sastanku od 12:00-16:00.','Zagreb',[('Gorivo (plaćeno poslovnom karticom)',False,0),('Gorivo (plaćeno poslovnom karticom)',False,0),('Čepin – Zagreb (cestarina)',True,17.20),('Zagreb – Čepin (cestarina)',True,17.20),('Parking 1',True,2.20),('Parking 2',True,8.00)])
insert_order('2026-4','2026-01-21',KARLA,KARLA,'Sastanak s klijentima – AMG','Arsano Medical Group d.o.o.','2026-01-21',1,46119,46686,fmt_dt('21/01/2025','05:35'),fmt_dt('21/01/2025','16:10'),0,10,25,0.5,30.0,15.0,64.70,79.70,'21.1. sastanak s Antom Mandićem u sjedištu softmana i s Mislavom Medvedom (PCP fond).\nZbog greške u očitanju ENC-a naplaćena maksimalna cestarina.','Zagreb',[('Cestarina Osijek-Zagreb',True,39.00),('Gorivo 1 (plaćeno službenom karticom)',False,0),('Cestarina Zagreb-Osijek',True,17.70),('Parking 1',True,8.00),('Gorivo 2 (plaćeno službenom karticom)',False,0)])
insert_order('2026-5','2026-01-26',KRESIMIR,KRESIMIR,'Sastanak s Meddox timom','Meddox Digital d.o.o.','2026-01-26',1,46730,47290,fmt_dt('26/01/2026','07:05'),fmt_dt('26/01/2026','18:30'),0,11,25,0.5,30.0,15.0,0.0,15.0,'Izvještavanje na NO Meddox Digital.','Zagreb',[('Gorivo (plaćeno poslovnom karticom)',False,0),('Gorivo (plaćeno poslovnom karticom)',False,0),('Čepin – Zagreb (cestarina, plaćeno poslovnom karticom)',False,0),('Zagreb – Čepin (cestarina, plaćeno poslovnom karticom)',False,0)])
insert_order('2026-6','2026-01-28',KARLA,KARLA,'Sastanak s klijentima – AMG','Arsano Medical Group d.o.o.','2026-01-28',1,47305,47863,fmt_dt('28/01/2026','04:55'),fmt_dt('28/01/2026','18:55'),0,14,0,1.0,30.0,30.0,17.70,47.70,'28.1. sastanak u D2000 i Q agenciji.\nPovratak starom cestom zbog prometne na autoputu.','Zagreb',[('Cestarina Osijek-Zagreb',True,17.70),('Gorivo 1 (plaćeno službenom karticom)',False,0),('Gorivo 2 (plaćeno službenom karticom)',False,0)])
insert_order('2026-7','2026-02-04',KRESIMIR,KRESIMIR,'Sastanak s Meddox timom','Meddox Digital d.o.o.','2026-02-04',1,47965,48540,fmt_dt('04/02/2026','07:45'),fmt_dt('04/02/2026','19:50'),0,12,5,1.0,30.0,30.0,22.20,52.20,'Sastanak u Poliklinici Aviva.','Zagreb',[('Gorivo (plaćeno poslovnom karticom)',False,0),('Gorivo (plaćeno poslovnom karticom)',False,0),('Čepin – Zagreb (cestarina, plaćeno poslovnom karticom)',False,0),('Zagreb – Čepin (plaćeno privatnom karticom)',True,17.20),('Parking 1',True,2.00),('Parking 2',True,1.60),('Parking 3',True,0.70),('Parking 4',True,0.70)])
insert_order('2026-8','2026-02-06',KARLA,KARLA,'Sastanak s klijentima – AMG','Arsano Medical Group d.o.o.','2026-02-06',1,48564,49140,fmt_dt('06/02/2026','06:00'),fmt_dt('06/02/2026','19:05'),0,13,5,1.0,30.0,30.0,40.10,70.10,'Odrađen sastanak u AMG-u vezano za tekuće implementacije, sastanak s predstavnikom Croatia Osiguranja te obilazak korisnika Dijagnostika 2000.','Zagreb',[('Cestarina Osijek-Zagreb (plaćeno privatnom karticom)',True,17.70),('Cestarina Zagreb-Osijek (plaćeno privatnom karticom)',True,17.70),('Gorivo 1 (plaćeno službenom karticom)',False,0),('Gorivo 2 (plaćeno službenom karticom)',False,0),('Parking 1',True,4.00),('Parking 2',True,0.70)])
insert_order('2026-9','2026-02-10',KARLA,KARLA,'Sastanak s klijentima – AMG','Arsano Medical Group d.o.o.','2026-02-10',2,49218,49806,fmt_dt('10/02/2026','05:30'),fmt_dt('11/02/2026','14:40'),1,9,10,1.5,30.0,45.0,38.70,83.70,'10.02. sastanak u Degordianu oko nadolazeće promjene strukture Interaktivnog studia.\n11.02. management meeting u AMG upravi.','Zagreb',[('Cestarina Osijek-Zagreb (plaćeno privatnom karticom)',True,17.70),('Cestarina Zagreb-Osijek (plaćeno privatnom karticom)',True,17.70),('Gorivo 1 (plaćeno službenom karticom)',False,0),('Gorivo 2 (plaćeno službenom karticom)',False,0),('Parking 1',True,0.30),('Parking 2',True,0.30),('Parking 3',True,0.30),('Parking 4',True,0.70),('Parking 5',True,0.70),('Parking 6',True,0.30),('Parking 7',True,0.70)])
insert_order('2026-10','2026-02-20',KRESIMIR,KRESIMIR,'Sastanak s Meddox timom','Meddox Digital d.o.o.','2026-02-20',1,50085,50534,fmt_dt('20/02/2026','07:15'),fmt_dt('20/02/2026','17:10'),0,9,55,0.5,30.0,15.0,27.80,42.80,'Sastanak u Mater agenciji (Euroart93).','Zagreb',[('Gorivo (plaćeno poslovnom karticom)',False,0),('Gorivo (plaćeno poslovnom karticom)',False,0),('Čepin – Popovača (plaćeno privatnom karticom)',True,13.90),('Popovača – Čepin (plaćeno privatnom karticom)',True,13.90)])
insert_order('2026-11','2026-02-23',KRESIMIR,KRESIMIR,'Sastanak s Meddox timom','Meddox Digital d.o.o.','2026-02-23',1,50607,51162,fmt_dt('23/02/2026','07:20'),fmt_dt('23/02/2026','18:15'),0,10,55,0.5,30.0,15.0,17.90,32.90,'Nadzorni odbor Meddox Digital. Sastanak CoreLine.','Zagreb',[('Gorivo (plaćeno poslovnom karticom)',False,0),('Gorivo (plaćeno poslovnom karticom)',False,0),('Čepin – Zagreb (plaćeno poslovnom karticom)',False,0),('Zagreb – Čepin (plaćeno privatnom karticom)',True,17.20),('Parking 1 (plaćeno poslovnom karticom)',False,0),('Parking 2 (plaćeno privatnom karticom)',True,0.70)])
insert_order('2026-12','2026-02-24',KARLA,KARLA,'Sastanak s klijentima – AMG','Arsano Medical Group d.o.o.','2026-02-24',2,51162,51758,fmt_dt('24/02/2026','06:00'),fmt_dt('25/02/2026','17:25'),1,10,55,1.5,30.0,45.0,3.70,48.70,'24.02. sastanak u Avivi oko HZZO računa te kasnije sastanak u Q agency oko partnership ugovora.\n25.02. management sastanak u AMG-u, zatim sastanak oko Meddox projekta i posjet Dijagnostici 2000.','Zagreb',[('Cestarina Osijek-Zagreb (plaćeno poslovnom karticom)',False,0),('Cestarina Zagreb-Osijek (plaćeno poslovnom karticom)',False,0),('Gorivo 1 (plaćeno službenom karticom)',False,0),('Gorivo 2 (plaćeno službenom karticom)',False,0),('Parking 1',True,0.70),('Parking 2',True,0.70),('Parking 3',True,0.70),('Parking 4',True,1.60)])

conn.execute("UPDATE settings SET value='12' WHERE key='last_order_number'")
conn.execute("UPDATE settings SET value='2026' WHERE key='last_order_year'")
conn.commit()
conn.close()
print("✅ Svih 12 putnih naloga uneseno!")

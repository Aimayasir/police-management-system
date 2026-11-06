"""
Police Station Management System - Database Seeder Script (Pakistani Localization)
Populates the database with realistic Pakistani police data across all 54 tables and 5 user roles.
"""

from datetime import datetime, date, timedelta
import random

from app import create_app
from app.models.base import db
from app.models import (
    Role, Permission, RolePermission, User, LoginLog,
    PoliceStation, Department, Rank, Designation, Officer,
    OfficerPosting, Shift, DutyRoster, Attendance, Leave,
    TrainingRecord, Transfer,
    FirStatus, CrimeCategory, CrimeType, FIR, Case,
    CaseStatusHistory, CaseOfficer, CaseNote, Court, Judge, CaseHearing,
    Complainant, Accused, Victim, Witness, CaseAccused,
    CaseVictim, CaseWitness, CriminalRecord, MissingPerson,
    EvidenceType, Evidence, EvidenceCustodyLog, LockupCell,
    Detainee, DetentionRecord, BailRecord,
    Vehicle, VehicleAssignment, Weapon, WeaponIssuance,
    InventoryItem, PatrolLog,
    Complaint, Notification, AuditLog, Document
)

app = create_app()

def seed_database():
    with app.app_context():
        print("[1/10] Resetting and re-creating database tables...")
        db.drop_all()
        db.create_all()

        print("[2/10] Seeding Roles & Permissions...")
        # 1. Roles
        roles_data = [
            ('Admin', 'ADM', 'Full system superuser with administrative privileges'),
            ('SHO', 'SHO', 'Station House Officer with full operational and custody command'),
            ('Inspector', 'INSP', 'Investigating Officer authorized for FIRs, case notes, and evidence'),
            ('Constable', 'CONST', 'Patrol and sentry personnel for duty rosters and attendance'),
            ('Clerk', 'CLK', 'Station Moharrir / clerical staff for complaint registry and records')
        ]
        roles = {}
        for name, code, desc in roles_data:
            r = Role(name=name, code=code, description=desc, status='active')
            db.session.add(r)
            roles[name] = r
        db.session.flush()

        # 2. Permissions
        perms_data = [
            ('View Dashboard', 'view_dashboard', 'main'),
            ('Register FIR', 'register_fir', 'firs'),
            ('Edit FIR', 'edit_fir', 'firs'),
            ('Delete FIR', 'delete_fir', 'firs'),
            ('Manage Cases', 'manage_cases', 'cases'),
            ('Add Case Notes', 'add_case_notes', 'cases'),
            ('Schedule Hearings', 'schedule_hearings', 'cases'),
            ('Manage Personnel', 'manage_personnel', 'officers'),
            ('Assign Duty Roster', 'assign_duty_roster', 'officers'),
            ('Mark Attendance', 'mark_attendance', 'officers'),
            ('Manage Detainees', 'manage_detainees', 'detainees'),
            ('Authorize Release', 'authorize_release', 'detainees'),
            ('Manage Evidence', 'manage_evidence', 'evidence'),
            ('Transfer Custody', 'transfer_custody', 'evidence'),
            ('Manage Fleet', 'manage_fleet', 'resources'),
            ('Manage Armory', 'manage_armory', 'resources'),
            ('Manage Complaints', 'manage_complaints', 'complaints'),
            ('Manage Users', 'manage_users', 'admin'),
            ('View Audit Logs', 'view_audit_logs', 'admin')
        ]
        permissions = []
        for name, code, mod in perms_data:
            p = Permission(name=name, code=code, module=mod, status='active')
            db.session.add(p)
            permissions.append(p)
        db.session.flush()

        # Role Permissions Junction
        for p in permissions:
            rp_admin = RolePermission(role_id=roles['Admin'].id, permission_id=p.id, status='active')
            db.session.add(rp_admin)
            if p.code != 'manage_users':
                rp_sho = RolePermission(role_id=roles['SHO'].id, permission_id=p.id, status='active')
                db.session.add(rp_sho)
            if p.module in ['main', 'firs', 'cases', 'evidence', 'detainees', 'complaints']:
                rp_insp = RolePermission(role_id=roles['Inspector'].id, permission_id=p.id, status='active')
                db.session.add(rp_insp)

        print("[3/10] Seeding Pakistani Police Stations, Ranks & Designations...")
        # 3. Police Stations (Pakistani cities)
        stations_data = [
            ('PS-CIVIL-LINES', 'Police Station Civil Lines', 'Lahore District', 'Civil Lines Division', 'The Mall Road, Near High Court', 'Lahore', 'Punjab', '54000', '+92-42-99201201', 'civillines.lhr@punjabpolice.gov.pk', 100),
            ('PS-SADDAR', 'Police Station Saddar', 'Rawalpindi District', 'Potohar Division', 'Kashmir Road, Saddar', 'Rawalpindi', 'Punjab', '46000', '+92-51-9292102', 'saddar.rwp@punjabpolice.gov.pk', 80),
            ('PS-CYBER-FIA', 'FIA Cyber Crime Reporting Centre', 'Islamabad District', 'Headquarters Division', 'Sector G-9/4, Mauve Area', 'Islamabad', 'Islamabad Capital Territory', '44000', '+92-51-9106003', 'complaints@fia.gov.pk', 50)
        ]
        stations = []
        for code, name, dist, div, addr, city, state, pin, phone, email, cap in stations_data:
            st = PoliceStation(
                station_code=code, name=name, district=dist, division=div,
                address=addr, city=city, state=state, postal_code=pin,
                contact_number=phone, email=email, capacity=cap, status='active'
            )
            db.session.add(st)
            stations.append(st)
        db.session.flush()

        # 4. Departments
        dept_data = [
            (stations[0].id, 'Investigation Branch (Tafteesh)', 'INVESTIGATION', 'Homicide, robbery, dacoity and heinous felony investigation'),
            (stations[0].id, 'Patrol & Operations Wing', 'OPERATIONS', 'Beat patrols, anti-car lifting picket checking, law & order'),
            (stations[0].id, 'Forensic & Evidence Malkhana', 'MALKHANA', 'Evidence locker, crime scene fingerprinting, arms depot'),
            (stations[2].id, 'Cyber Crime Investigation Wing', 'CYBER', 'Online banking scams, extortion, harassment & PECA offenses')
        ]
        departments = []
        for st_id, d_name, d_code, d_desc in dept_data:
            dept = Department(station_id=st_id, name=d_name, code=d_code, description=d_desc, status='active')
            db.session.add(dept)
            departments.append(dept)
        db.session.flush()

        # 5. Ranks (Pakistan Police hierarchy)
        ranks_data = [
            ('Inspector General of Police (IGP)', 1, 'IGP'),
            ('Deputy Inspector General (DIG)', 2, 'DIG'),
            ('Senior Superintendent of Police (SSP)', 3, 'SSP'),
            ('Superintendent of Police (SP)', 4, 'SP'),
            ('Deputy Superintendent of Police (DSP)', 5, 'DSP'),
            ('Inspector of Police', 6, 'INSP'),
            ('Sub-Inspector (SI)', 7, 'SI'),
            ('Assistant Sub-Inspector (ASI)', 8, 'ASI'),
            ('Head Constable (HC)', 9, 'HC'),
            ('Constable', 10, 'CONST')
        ]
        ranks = {}
        for r_name, r_lvl, r_ins in ranks_data:
            rk = Rank(name=r_name, rank_level=r_lvl, insignia_code=r_ins, status='active')
            db.session.add(rk)
            ranks[r_name] = rk
        db.session.flush()

        # 6. Designations
        desigs_data = [
            ('Station House Officer (SHO)', 'SHO', 'In charge of police station territorial command'),
            ('In-Charge Investigation (Chowki / Circle)', 'LEAD_IO', 'Heads crime investigation branch'),
            ('Head Moharrir (Station Clerk)', 'MOHARRIR', 'Station record clerk and case register in-charge'),
            ('Malkhana Custodian (Evidence Keeper)', 'MALKHANA_INCH', 'Arms, recovered property and evidence custodian'),
            ('Lockup Guard & Sentry In-Charge', 'LOCK_INCH', 'Detainee custody, remand diary and hawalat security')
        ]
        designations = {}
        for t, c, d in desigs_data:
            ds = Designation(title=t, code=c, description=d, status='active')
            db.session.add(ds)
            designations[c] = ds
        db.session.flush()

        print("[4/10] Seeding Pakistani Users & Police Personnel...")
        # 7. Users & Officers with Pakistani Names & Numbers
        users_seed = [
            ('admin', 'admin@police.gov.pk', 'admin123', 'Tariq Mehmood', 'ADM-001', '+92 300 0000001', 'Admin', stations[0].id, 'Inspector of Police', 'SHO'),
            ('sho', 'sho.asad@punjabpolice.gov.pk', 'admin123', 'Malik Asad', 'LHR-PS-1001', '+92 300 1122334', 'SHO', stations[0].id, 'Inspector of Police', 'SHO'),
            ('inspector', 'hamza.ali@punjabpolice.gov.pk', 'admin123', 'Hamza Ali', 'LHR-PS-2045', '+92 321 4455667', 'Inspector', stations[0].id, 'Sub-Inspector (SI)', 'LEAD_IO'),
            ('constable', 'rizwan@punjabpolice.gov.pk', 'admin123', 'Muhammad Rizwan', 'LHR-PS-3088', '+92 333 5566778', 'Constable', stations[0].id, 'Constable', 'MOHARRIR'),
            ('clerk', 'ayesha.khan@punjabpolice.gov.pk', 'admin123', 'Ayesha Khan', 'LHR-PS-4012', '+92 345 6677889', 'Clerk', stations[0].id, 'Assistant Sub-Inspector (ASI)', 'MOHARRIR')
        ]

        created_officers = []
        for uname, uemail, upass, ufullname, ubadge, uphone, urole, ust_id, urank, udesig in users_seed:
            user = User(
                username=uname,
                email=uemail,
                full_name=ufullname,
                badge_number=ubadge,
                phone=uphone,
                role_id=roles[urole].id,
                station_id=ust_id,
                is_active_account=True,
                status='active'
            )
            user.set_password(upass)
            db.session.add(user)
            db.session.flush()

            officer = Officer(
                user_id=user.id,
                station_id=ust_id,
                department_id=departments[0].id if 'Inspector' in urank or 'SHO' in urole else departments[1].id,
                rank_id=ranks[urank].id,
                designation_id=designations[udesig].id,
                badge_number=ubadge,
                first_name=ufullname.split()[0],
                last_name=ufullname.split()[1] if len(ufullname.split()) > 1 else 'Khan',
                date_of_birth=date(1987, 8, 14),
                gender='Male' if 'Ayesha' not in ufullname else 'Female',
                blood_group='B+',
                contact_phone=uphone,
                email=uemail,
                emergency_contact='Brother / Spouse: +92 322 8899001',
                joining_date=date(2016, 3, 23),
                salary=115000.00 if urole in ['Admin', 'SHO'] else (85000.00 if urole == 'Inspector' else 55000.00),
                current_status='On Duty',
                status='active'
            )
            db.session.add(officer)
            created_officers.append(officer)
        db.session.flush()

        # Seed sample login logs
        for u in created_officers[:2]:
            ll = LoginLog(
                user_id=u.user_id,
                ip_address='127.0.0.1',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) PSMS/Terminal',
                login_time=datetime.utcnow() - timedelta(hours=2),
                status_message='SUCCESS',
                status='active'
            )
            db.session.add(ll)

        stations[0].sho_officer_id = created_officers[1].id
        db.session.commit()

        # 8. Shifts
        shifts_data = [
            ('Morning Shift', '06:00', '14:00', 8, 'Daytime beat patrol, commercial market security and morning roll call'),
            ('Evening Shift', '14:00', '22:00', 8, 'Rush hour traffic management, shopping zone security, peak public desk'),
            ('Night Shift (Ghasht)', '22:00', '06:00', 8, 'Night picket checking, naka bandi, highway surveillance, hawalat vigil')
        ]
        shifts = []
        for s_name, s_start, s_end, s_dur, s_desc in shifts_data:
            sh = Shift(name=s_name, start_time=s_start, end_time=s_end, duration_hours=s_dur, description=s_desc, status='active')
            db.session.add(sh)
            shifts.append(sh)
        db.session.flush()

        # 9. Duty Rosters & Attendance for today
        today = date.today()
        areas = ['The Mall Road Commercial Beat', 'Anarkali Bazaar Entrance', 'High Court Chowk Picket', 'Canal Bank Road Sector 4']
        for i, off in enumerate(created_officers):
            r = DutyRoster(
                station_id=stations[0].id,
                officer_id=off.id,
                shift_id=shifts[i % len(shifts)].id,
                duty_date=today,
                assigned_area=areas[i % len(areas)],
                duty_type='Beat Patrol (Ghasht)' if i % 2 == 0 else 'Station Desk / Hawalat Guard',
                remarks='Standard operational arms & wireless radio issued',
                status='active'
            )
            db.session.add(r)

            att = Attendance(
                officer_id=off.id,
                station_id=stations[0].id,
                attendance_date=today,
                check_in_time=datetime.utcnow() - timedelta(hours=i+1),
                attendance_status='Present',
                remarks='On time for morning parade & roll-call',
                status='active'
            )
            db.session.add(att)

        # 9b. Officer Postings, Leaves, Training Records & Transfers
        for off in created_officers:
            posting = OfficerPosting(
                officer_id=off.id,
                station_id=stations[0].id,
                department_id=departments[0].id,
                role_title=f"{off.rank.name if off.rank else 'Duty Officer'} - Operational Command",
                start_date=date(2025, 1, 15),
                transfer_order_number='DIG-LHR-ORDER-2025-104',
                remarks='Active deployment under Lahore Capital City Police',
                status='active'
            )
            db.session.add(posting)

        sample_leave = Leave(
            officer_id=created_officers[3].id,
            leave_type='Casual Leave',
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=7),
            total_days=3,
            reason='Family emergency and sister marriage ceremony in Faisalabad',
            approval_status='Approved',
            approved_by_officer_id=created_officers[1].id,
            approval_date=date.today() - timedelta(days=12),
            status='active'
        )
        db.session.add(sample_leave)

        trainings_data = [
            (created_officers[1].id, 'Advanced Homicide Crime Scene Management', 'Police College Sihala (Rawalpindi)', date(2024, 3, 1), date(2024, 3, 28), 'Certified Homicide Investigator (Level-3)', 'A+', 'Passed with Distinction'),
            (created_officers[2].id, 'PFSA Forensic Evidence Collection & Cyber Analysis', 'Punjab Forensic Science Agency (PFSA) Lahore', date(2024, 6, 10), date(2024, 6, 25), 'Certified Forensic First Responder', 'A', 'Passed')
        ]
        for off_id, cname, inst, sdate, edate, cert, grd, res in trainings_data:
            tr = TrainingRecord(
                officer_id=off_id,
                course_name=cname,
                training_institution=inst,
                start_date=sdate,
                end_date=edate,
                certification_name=cert,
                grade=grd,
                result=res,
                status='active'
            )
            db.session.add(tr)

        trans = Transfer(
            officer_id=created_officers[1].id,
            from_station_id=stations[1].id,
            to_station_id=stations[0].id,
            transfer_order_date=date(2025, 1, 10),
            effective_date=date(2025, 1, 15),
            reason='Routine administrative rotational posting of Station House Officers',
            order_reference_number='IGP-PUNJAB-TRANS-2025-8891',
            approved_by_user_id=created_officers[0].user_id,
            status='active'
        )
        db.session.add(trans)

        print("[5/10] Seeding Pakistan Penal Code (PPC) Offenses & FIR Statuses...")
        # 10. FIR Statuses
        statuses_data = [
            ('Registered', 'REG', 'FIR formally registered in Roznamcha and assigned number', 'secondary'),
            ('Under Investigation', 'INV', 'Investigation Officer (Tafteesh) examining evidence & witnesses', 'warning text-dark'),
            ('Challan Submitted', 'CSF', 'Challan under CrPC 173 submitted before Area Magistrate', 'info text-dark'),
            ('Under Trial in Court', 'CRT', 'Trial proceedings actively underway before Sessions Court', 'primary'),
            ('Disposed / Closed', 'CLS', 'Case decided, accused convicted/acquitted or cancelled by court order', 'success')
        ]
        fir_statuses = []
        for st_name, st_code, st_desc, st_badge in statuses_data:
            fs = FirStatus(name=st_name, code=st_code, description=st_desc, color_badge=st_badge, status='active')
            db.session.add(fs)
            fir_statuses.append(fs)
        db.session.flush()

        # 11. Crime Categories & Types (PPC & PECA)
        cats_data = [
            ('Crimes Against Person (Jurm-e-Zarrar)', 'PERSON', 'Offenses against human life, murder, assault, kidnapping'),
            ('Property Crimes (Jurm-e-Maal)', 'PROP', 'Robbery (Dacoity), burglary, theft, extortion'),
            ('Cyber Crimes (PECA 2016)', 'CYBER', 'Electronic fraud, online financial theft, blackmailing'),
            ('Narcotics Control (CNSA 1997)', 'DRUG', 'Illicit drug trafficking and smuggling under Anti-Narcotics laws')
        ]
        crime_types = []
        for c_name, c_code, c_desc in cats_data:
            cat = CrimeCategory(name=c_name, code=c_code, description=c_desc, status='active')
            db.session.add(cat)
            db.session.flush()

            if c_code == 'PERSON':
                ct1 = CrimeType(category_id=cat.id, name='Qatl-i-Amd (Murder)', code='MURDER', relevant_sections='PPC Section 302 / 34', severity_level='Critical', status='active')
                ct2 = CrimeType(category_id=cat.id, name='Attempted Murder (Iqdam-e-Qatl)', code='ASSAULT', relevant_sections='PPC Section 324', severity_level='High', status='active')
                db.session.add_all([ct1, ct2])
                crime_types.extend([ct1, ct2])
            elif c_code == 'PROP':
                ct3 = CrimeType(category_id=cat.id, name='Armed Dacoity / Robbery (Rahzani)', code='ROBBERY', relevant_sections='PPC Section 392 / 395', severity_level='High', status='active')
                ct4 = CrimeType(category_id=cat.id, name='Night Housebreaking & Burglary (Naqb Zani)', code='BURGLARY', relevant_sections='PPC Section 457 / 380', severity_level='Medium', status='active')
                db.session.add_all([ct3, ct4])
                crime_types.extend([ct3, ct4])
            elif c_code == 'CYBER':
                ct5 = CrimeType(category_id=cat.id, name='Online Financial Fraud / Phishing', code='CYBER_FRAUD', relevant_sections='PECA 2016 Section 13 / PPC 420', severity_level='Medium', status='active')
                db.session.add(ct5)
                crime_types.append(ct5)
            elif c_code == 'DRUG':
                ct6 = CrimeType(category_id=cat.id, name='Commercial Drug Trafficking (Manashiyat)', code='CNSA_TRAFFICK', relevant_sections='CNSA 1997 Section 9(c)', severity_level='High', status='active')
                db.session.add(ct6)
                crime_types.append(ct6)
        db.session.flush()

        print("[6/10] Seeding Pakistani Courts, Judges, Complainants & FIRs...")
        # 12. Courts & Judges (Pakistani Judiciary)
        court = Court(
            name='District & Sessions Court, Lahore',
            court_type='Sessions Court',
            district='Lahore District',
            jurisdiction_area='Civil Lines & Sadar Sub-Divisions',
            contact_number='+92-42-99211011',
            address='Sessions Court Complex, Lower Mall, Lahore',
            status='active'
        )
        db.session.add(court)
        db.session.flush()

        judge = Judge(
            court_id=court.id,
            full_name='Hon. Justice Shahid Rafiq',
            designation='Additional Sessions Judge',
            room_number='Courtroom 12',
            contact_number='+92-42-99211012',
            email='court12.lhr@lhc.gov.pk',
            status='active'
        )
        db.session.add(judge)
        db.session.flush()

        # 13. Complainants (Pakistani citizens with CNIC & Pakistani phone numbers)
        complainants_data = [
            ('Muhammad Usman', 'Abdul Rehman', date(1984, 4, 12), 'Male', '35201-4482901-3', '+92 300 8472911', 'usman.traders@gmail.com', 'House 42, Block C, Gulberg III, Lahore'),
            ('Zainab Bibi', 'Tariq Jameel', date(1992, 9, 21), 'Female', '35202-9811234-2', '+92 322 9988112', 'zainab.tariq@yahoo.com', 'Flat 14, Shadman Colony, Lahore'),
            ('Bilal Ahmed', 'Rashid Ahmed', date(1980, 1, 15), 'Male', '37405-3341998-1', '+92 333 7766554', 'bilal.ahmed@paktech.pk', 'House 108, Street 12, Sector F-10/2, Islamabad')
        ]
        complainants = []
        for c_name, c_father, c_dob, c_gender, c_nid, c_phone, c_email, c_addr in complainants_data:
            comp = Complainant(
                full_name=c_name, father_or_spouse_name=c_father, date_of_birth=c_dob,
                gender=c_gender, national_id=c_nid, phone=c_phone, email=c_email,
                address=c_addr, occupation='Trader / Businessman', status='active'
            )
            db.session.add(comp)
            complainants.append(comp)
        db.session.flush()

        firs_seed = [
            ('FIR-LHR-20261015-1042', stations[0].id, crime_types[2].id, complainants[0].id, fir_statuses[1].id, created_officers[2].id, datetime.utcnow() - timedelta(days=12), 'Shop 14, The Mall Road, Lahore', '500 meters East', 'Two armed masked dacoits on a red Honda 125 entered the jewelry shop at gunpoint, held the cashier hostage, and looted PKR 3,50,000 in cash along with gold ornaments before escaping towards Anarkali.', True),
            ('FIR-LHR-20261022-2091', stations[0].id, crime_types[4].id, complainants[2].id, fir_statuses[1].id, created_officers[2].id, datetime.utcnow() - timedelta(days=7), 'Online Easypaisa / HBL Mobile Banking', 'N/A', 'Complainant reported unauthorized electronic transfer of PKR 4,20,000 via a fraudulent spoofing call posing as bank helpline seeking biometric verification.', False),
            ('FIR-LHR-20261029-3312', stations[0].id, crime_types[0].id, complainants[1].id, fir_statuses[0].id, created_officers[1].id, datetime.utcnow() - timedelta(days=2), 'Near Ravi River Bridge Bank, Lahore', '1.2 KM North', 'Local night patrol recovered unidentified male body aged approx 35 years showing severe blunt force cranial injuries. Case registered under Qatl-i-Amd PPC 302.', True)
        ]
        created_firs = []
        for f_num, f_st, f_crime, f_comp, f_status, f_io, f_time, f_loc, f_dist, f_details, f_cog in firs_seed:
            fir = FIR(
                fir_number=f_num,
                station_id=f_st,
                crime_type_id=f_crime,
                complainant_id=f_comp,
                current_status_id=f_status,
                registered_by_user_id=created_officers[0].user_id,
                io_officer_id=f_io,
                incident_date_time=f_time,
                incident_location=f_loc,
                distance_from_station=f_dist,
                incident_details=f_details,
                is_cognizable=f_cog,
                status='active'
            )
            db.session.add(fir)
            created_firs.append(fir)
        db.session.flush()

        print("[7/10] Seeding Cases, Accused (Pakistani Suspects), Hearings & Zimni Notes...")
        # 14. Cases
        case1 = Case(
            case_number='CASE-2026-89101',
            fir_id=created_firs[0].id,
            station_id=stations[0].id,
            lead_investigator_id=created_officers[2].id,
            crime_type_id=created_firs[0].crime_type_id,
            court_id=court.id,
            case_title='State vs. Akram @ Bhola & Anr (The Mall Armed Dacoity)',
            case_status='Under Investigation',
            date_opened=date.today() - timedelta(days=10),
            summary='Armed robbery investigation under PPC 392/395 at The Mall jewelry shop. Suspect motorbike traced through Safe City Authority CCTV surveillance.',
            status='active'
        )
        db.session.add(case1)
        db.session.flush()

        c_hist = CaseStatusHistory(
            case_id=case1.id,
            previous_status='Registered',
            new_status='Under Investigation',
            changed_by_user_id=created_officers[1].user_id,
            comments='Case docket and Zimni diary initiated following CCTV facial match',
            status='active'
        )
        db.session.add(c_hist)

        co1 = CaseOfficer(case_id=case1.id, officer_id=created_officers[2].id, role_in_case='Lead Investigating Officer (Tafteesh)', assigned_date=date.today() - timedelta(days=10), status='active')
        co2 = CaseOfficer(case_id=case1.id, officer_id=created_officers[3].id, role_in_case='Field Raid & Apprehension Unit', assigned_date=date.today() - timedelta(days=9), status='active')
        db.session.add_all([co1, co2])

        # Case Notes (Zimniyat)
        cn1 = CaseNote(
            case_id=case1.id,
            officer_id=created_officers[2].id,
            note_date=datetime.utcnow() - timedelta(days=8),
            title='Zimni 1: Punjab Safe City Camera Footage Review',
            content='Examined Safe City cameras at Mall Road chowk. Observed Honda 125 red motorcycle without registration plate carrying two pillion riders wearing black jackets escaping towards Bhati Gate.',
            is_confidential=False,
            status='active'
        )
        cn2 = CaseNote(
            case_id=case1.id,
            officer_id=created_officers[2].id,
            note_date=datetime.utcnow() - timedelta(days=4),
            title='Zimni 2: Mukhbir-e-Khas (Secret Informant) Tip',
            content='Confidential police informant confirmed suspect Akram @ Bhola was spotted hiding in an illegal warehouse in Badami Bagh area.',
            is_confidential=True,
            status='active'
        )
        db.session.add_all([cn1, cn2])

        hearing = CaseHearing(
            case_id=case1.id,
            court_id=court.id,
            judge_id=judge.id,
            hearing_date=date.today() + timedelta(days=7),
            hearing_time='10:30 AM',
            hearing_type='Bail Hearing',
            outcome='Pending Court Hearing',
            judge_remarks='Police remand report and recovery memo directed for presentation',
            status='active'
        )
        db.session.add(hearing)

        # 15. Accused (Pakistani Suspect)
        accused1 = Accused(
            full_name='Akram Shehzad',
            alias='Bhola / Commando',
            date_of_birth=date(1992, 6, 18),
            gender='Male',
            national_id='35202-7788112-9',
            phone='+92 301 9988776',
            address='Street 5, Mohallah Chah Miran, Lahore',
            physical_features='Height 5ft 10in, surgical scar on left cheek, tattoo on right wrist',
            nationality='Pakistani',
            is_in_custody=True,
            status='active'
        )
        db.session.add(accused1)
        db.session.flush()

        case_acc = CaseAccused(
            case_id=case1.id,
            accused_id=accused1.id,
            charges_framed='PPC Section 392 (Robbery), PPC Section 397 (Robbery with attempt to cause grievous hurt)',
            arrest_status='Detained',
            arrest_date=date.today() - timedelta(days=2),
            status='active'
        )
        db.session.add(case_acc)

        crim_rec = CriminalRecord(
            accused_id=accused1.id,
            person_name='Akram Shehzad',
            alias='Bhola',
            criminal_id_code='CRIM-PK-2021-9982',
            finger_print_ref='FP-LHR-8821',
            criminal_history_summary='History-sheeter with 2 previous burglary challans in Badami Bagh and 1 illegal arms recovery case under 13/20/65.',
            known_gang_affiliation='Nadeem Boxer Gang',
            previous_convictions_count=2,
            risk_level='High',
            status='active'
        )
        db.session.add(crim_rec)

        # 15b. Victims and Case Victims
        victim1 = Victim(
            full_name='Tariq Aziz',
            date_of_birth=date(1982, 5, 14),
            gender='Male',
            national_id='35201-1988223-1',
            phone='+92 300 7766551',
            address='Al-Rehman Plaza, The Mall Lahore',
            medical_report_summary='Laceration on right arm caused by blunt weapon impact during shop dacoity. Treated at Mayo Hospital Emergency.',
            injury_status='Minor Bludgeon Wounds',
            contact_person='Wife: Bushra Bibi (+92 300 7766552)',
            status='active'
        )
        db.session.add(victim1)
        db.session.flush()

        cv1 = CaseVictim(
            case_id=case1.id,
            victim_id=victim1.id,
            statement_taken=True,
            victim_statement='Robber with black face mask entered shop brandishing 30-bore pistol, demanding showcase keys.',
            statement_date=date.today() - timedelta(days=9),
            status='active'
        )
        db.session.add(cv1)

        # 15c. Witnesses and Case Witnesses
        witness1 = Witness(
            full_name='Muhammad Shafi',
            date_of_birth=date(1978, 11, 20),
            gender='Male',
            national_id='35202-6677881-3',
            phone='+92 321 4433229',
            address='Shop 12, Anarkali Commercial Market, Lahore',
            witness_type='Eye Witness',
            protection_required=False,
            status='active'
        )
        db.session.add(witness1)
        db.session.flush()

        cw1 = CaseWitness(
            case_id=case1.id,
            witness_id=witness1.id,
            statement_summary='Saw two armed suspects flee towards Hall Road on a black Honda 125 motorcycle.',
            statement_date=date.today() - timedelta(days=9),
            is_hostile=False,
            status='active'
        )
        db.session.add(cw1)

        print("[8/10] Seeding Police Lockup (Hawalat), Detainees & Custody Records...")
        # 16. Lockup Cells (Hawalat)
        cells_data = [
            (stations[0].id, '01', 'General Male Hawalat Cell A', 'General', 6, 1, 'Reinforced Steel Bars, Clean Sanitation', 'High'),
            (stations[0].id, '02', 'General Male Hawalat Cell B', 'General', 6, 0, 'Reinforced Steel Bars', 'High'),
            (stations[0].id, '03', 'Female Hawalat (Zanana Hawalat)', 'Female', 3, 0, 'Separated Sanitary & Sleeping Quarters with Lady Constable Duty', 'Standard'),
            (stations[0].id, '04', 'High-Security Solitary Cell (Tanhai)', 'Solitary', 1, 0, 'CCTV Monitored Solitary Unit', 'Maximum')
        ]
        cells = []
        for st_id, num, cname, ctype, cap, occ, cond, sec in cells_data:
            cell = LockupCell(
                station_id=st_id, cell_number=num, cell_name=cname, cell_type=ctype,
                capacity=cap, current_occupancy=occ, cell_condition=cond, security_level=sec,
                status='active'
            )
            db.session.add(cell)
            cells.append(cell)
        db.session.flush()

        # 17. Detainees
        detainee = Detainee(
            accused_id=accused1.id,
            full_name=accused1.full_name,
            alias=accused1.alias,
            national_id=accused1.national_id,
            gender=accused1.gender,
            age=34,
            blood_group='O+',
            personal_belongings='1x Leather wallet containing PKR 1,420 cash and CNIC card, 1x Infinix Hot 12 mobile phone, 1x silver ring, 1x black leather belt.',
            health_condition='Physical medical examination conducted at Mayo Hospital Lahore. Medically fit for police lockup.',
            emergency_contact='Brother: Tariq Shehzad (+92 302 4433221)',
            status='active'
        )
        db.session.add(detainee)
        db.session.flush()

        det_record = DetentionRecord(
            detainee_id=detainee.id,
            cell_id=cells[0].id,
            case_id=case1.id,
            fir_id=created_firs[0].id,
            arresting_officer_id=created_officers[2].id,
            arrest_date_time=datetime.utcnow() - timedelta(days=2),
            detention_reason='Apprehended in connection with The Mall jewelry robbery under PPC 392/397. Illegal 30-bore weapon recovered.',
            medical_examination_done=True,
            doctor_name='Dr. Farhan Qureshi (Mayo Hospital Lahore)',
            detention_status='In Custody',
            status='active'
        )
        db.session.add(det_record)
        db.session.flush()

        # 17b. Bail Records
        bail1 = BailRecord(
            detention_record_id=det_record.id,
            case_id=case1.id,
            court_id=court.id,
            surety_name='Bashir Ahmed',
            surety_contact='+92 302 9988112',
            surety_national_id='35201-4455667-1',
            bail_amount=50000.00,
            bail_granted_date=datetime.utcnow() - timedelta(days=1),
            bail_order_reference='CML-BAIL-ORDER-2026-4412',
            bail_conditions='Accused shall surrender original passport, report to IO every Monday at 10 AM, and furnish personal surety bond.',
            lawyer_name='Advocate Ch. Zulfiqar Ali (Lahore High Court Bar)',
            status='active'
        )
        db.session.add(bail1)

        # 17c. Missing Persons
        mp1 = MissingPerson(
            report_number='MP-202610-091',
            station_id=stations[0].id,
            reporting_person_name='Sultan Raza',
            contact_phone='+92 301 5544332',
            missing_person_name='Ahmed Raza',
            age=14,
            gender='Male',
            date_last_seen=date.today() - timedelta(days=5),
            place_last_seen='Near Data Darbar Gate 3, Lahore',
            physical_description='Birthmark on left forearm, scar near right eyebrow, height approx 5 ft',
            clothing_description='Wearing blue shalwar kameez and black plastic slippers',
            status_resolution='Active Search',
            io_officer_id=created_officers[2].id,
            status='active'
        )
        db.session.add(mp1)

        print("[9/10] Seeding Evidence Types, Items & Malkhana Chain of Custody...")
        # 18. Evidence Types
        evd_types_data = [
            ('Physical Evidence (Maal-e-Muqaddama)', 'PHYSICAL', 'Store in dry sealed tamper-proof canvas bag'),
            ('Ballistic / Firearm & Spent Casings', 'BALLISTIC', 'Unload weapon, preserve fingerprints, tag serial for Punjab Forensic Science Agency (PFSA)'),
            ('Digital / Cyber Devices', 'DIGITAL', 'Faraday bag shielding from network signals'),
            ('Biological / DNA Specimen', 'BIO', 'Temperature controlled refrigerated evidence locker')
        ]
        evd_types = []
        for name, code, proto in evd_types_data:
            et = EvidenceType(name=name, code=code, handling_protocol=proto, status='active')
            db.session.add(et)
            evd_types.append(et)
        db.session.flush()

        # 19. Evidence Items
        evd1 = Evidence(
            evidence_number='EVD-202610-8801',
            case_id=case1.id,
            fir_id=created_firs[0].id,
            evidence_type_id=evd_types[1].id,
            collected_by_officer_id=created_officers[2].id,
            item_name='30 Bore TT Pistol (Peshawar Made) with Magazine',
            description='Country-made 30 bore pistol with brown grip. Serial # TT-91024. Magazine containing 4 live rounds.',
            collected_from_location='Recovered from suspect waistband during raid in Badami Bagh',
            collected_at_datetime=datetime.utcnow() - timedelta(days=2),
            current_storage_location='Malkhana Strongbox Safe #4',
            condition_description='Intact with traces of gun oil. Sealed in parcel with red sealing wax.',
            chain_of_custody_status='In Locker',
            barcode='BAR-PK-881122',
            status='active'
        )
        evd2 = Evidence(
            evidence_number='EVD-202610-8802',
            case_id=case1.id,
            fir_id=created_firs[0].id,
            evidence_type_id=evd_types[0].id,
            collected_by_officer_id=created_officers[2].id,
            item_name='Recovered Robbery Cash (PKR 1,80,000)',
            description='Pakistani currency notes: 30x Rs. 5000 notes and 30x Rs. 1000 notes bundled in plastic packet.',
            collected_from_location='Recovered from suspect hideout wardrobe',
            collected_at_datetime=datetime.utcnow() - timedelta(days=2),
            current_storage_location='Malkhana Valuables Safe 1',
            condition_description='Signed and verified by independent recovery memo witnesses.',
            chain_of_custody_status='In Locker',
            barcode='BAR-PK-881123',
            status='active'
        )
        db.session.add_all([evd1, evd2])
        db.session.flush()

        clog1 = EvidenceCustodyLog(
            evidence_id=evd1.id,
            transferred_from_user_id=created_officers[2].user_id,
            transferred_to_user_id=created_officers[1].user_id,
            transfer_date=datetime.utcnow() - timedelta(days=2),
            transfer_purpose='Initial Seizure & Malkhana Deposit',
            source_location='Crime Scene Badami Bagh',
            destination_location='Malkhana Strongbox Safe #4',
            receipt_ack='MALKHANA-ENTRY-412',
            status='active'
        )
        db.session.add(clog1)

        print("[10/10] Seeding Pakistani Patrol Vehicles, POF Weapons & Citizen Complaints...")
        # 20. Vehicles (Pakistani Police fleet numbers)
        vehicles_data = [
            (stations[0].id, 'LEA-23-1001', 'Patrol Car', 'Toyota Hilux Single Cabin Police Mobile', 2023, 'Diesel', 'Available', 24150),
            (stations[0].id, 'LEG-24-1002', 'SUV', 'Toyota Corolla GLi Patrol Interceptor', 2024, 'Petrol', 'On Patrol', 14200),
            (stations[0].id, 'LEV-21-1003', 'Prisoner Van', 'Hino Reinforced Qaidi Prisoner Van', 2021, 'Diesel', 'Available', 52300),
            (stations[0].id, 'LEM-24-1004', 'Motorcycle', 'Honda 125 Dolphin Squad Patrol Bike', 2024, 'Petrol', 'On Patrol', 7600)
        ]
        vehicles = []
        for st_id, reg, vtype, make, yr, fuel, ops, odo in vehicles_data:
            veh = Vehicle(
                station_id=st_id, registration_number=reg, vehicle_type=vtype,
                make_model=make, year=yr, fuel_type=fuel, operational_status=ops,
                current_odometer_km=odo, status='active'
            )
            db.session.add(veh)
            vehicles.append(veh)
        db.session.flush()

        # 21. Weapons (POF & Police Service Weapons)
        weapons_data = [
            (stations[0].id, 'POF-MP5-9011', 'MP5 9mm Submachine Gun (POF)', '9x19mm Parabellum', 'Good', 'Kot Rack A-01', 30),
            (stations[0].id, 'POF-MP5-9012', 'MP5 9mm Submachine Gun (POF)', '9x19mm Parabellum', 'Good', 'Kot Rack A-02', 30),
            (stations[0].id, 'POF-G3-44120', 'G3A3 7.62mm Assault Rifle (POF Wah)', '7.62x51mm NATO', 'Good', 'Kot Rack B-01', 20),
            (stations[0].id, 'GLK-19-PK-88', 'Glock 19 9mm Pistol', '9x19mm', 'Good', 'Kot Safe C-01', 15)
        ]
        created_weapons = []
        for st_id, sn, wtype, cal, cond, rack, cap in weapons_data:
            wep = Weapon(
                station_id=st_id, serial_number=sn, weapon_type=wtype,
                caliber=cal, condition=cond, storage_rack_number=rack,
                ammunition_capacity=cap, status='active'
            )
            db.session.add(wep)
            created_weapons.append(wep)
        db.session.flush()

        # 22. Inventory Items
        inv_data = [
            (stations[0].id, 'Tactical Gear', 'Bulletproof Kevlar Tactical Armor Vest (POF)', 25, 20, 'units', 'Kot Supply Room', 5),
            (stations[0].id, 'Radios & Comms', 'Motorola Police Wireless Two-Way Handset', 35, 28, 'units', 'Wireless Control Room', 6),
            (stations[0].id, 'Forensics Kits', 'Punjab Forensic Science Agency (PFSA) Evidence Seizure Kit', 6, 5, 'kits', 'Investigation Office', 2),
            (stations[0].id, 'First Aid / Medical', 'Emergency Trauma Tactical Medical Kit', 12, 10, 'kits', 'Duty Officer Room', 3)
        ]
        for st_id, cat, iname, tot, avail, uom, loc, reord in inv_data:
            inv = InventoryItem(
                station_id=st_id, item_category=cat, item_name=iname,
                total_quantity=tot, available_quantity=avail, unit_of_measure=uom,
                storage_location=loc, reorder_level=reord, status='active'
            )
            db.session.add(inv)

        # 23. Citizen Complaints (Pakistani public petitions)
        complaints_data = [
            ('CMP-202610-101', 'Saima Rashid', '+92 301 5566778', 'saima.rashid@gmail.com', 'House 15, Sector B, DHA Phase 5, Lahore', stations[0].id, 'Late-Night Marriage Hall Loudspeaker & Aerial Firing', 'Local banquet hall operating loud amplified sound system past 10 PM and occasional celebratory aerial firing creating public panic.', 'High', 'Under Inquiry'),
            ('CMP-202610-102', 'Kamran Aslam', '+92 321 8877665', 'kamran.aslam@outlook.com', 'Shop 8, G-11 Markaz, Islamabad', stations[0].id, 'Motorcycle Theft from Mosque Parking', 'Super Power 70cc motorcycle was stolen outside Jamia Mosque during Friday prayers.', 'Low', 'Pending')
        ]
        for cnum, cname, cphone, cemail, caddr, st_id, subj, desc, prio, res in complaints_data:
            cmp = Complaint(
                complaint_number=cnum, citizen_name=cname, citizen_phone=cphone,
                citizen_email=cemail, citizen_address=caddr, station_id=st_id,
                subject=subj, description=desc, priority=prio, resolution_status=res,
                complaint_date=datetime.utcnow() - timedelta(days=3), status='active'
            )
            db.session.add(cmp)

        # 23b. Vehicle Assignments, Weapon Issuances & Patrol Logs
        va1 = VehicleAssignment(
            vehicle_id=vehicles[0].id,
            officer_id=created_officers[3].id,
            assignment_date=date.today(),
            purpose='Mall Road and High Court Sector mobile patrolling',
            start_km=42150,
            fuel_issued_liters=25.0,
            status_remarks='Vehicle checked, siren, wireless and flasher lights fully operational',
            status='active'
        )
        db.session.add(va1)

        wi1 = WeaponIssuance(
            weapon_id=created_weapons[0].id,
            officer_id=created_officers[3].id,
            issued_by_officer_id=created_officers[4].id,
            issue_datetime=datetime.utcnow() - timedelta(hours=4),
            rounds_issued=30,
            rounds_discharged=0,
            status='active'
        )
        db.session.add(wi1)

        pl1 = PatrolLog(
            station_id=stations[0].id,
            vehicle_id=vehicles[0].id,
            lead_officer_id=created_officers[2].id,
            route_name='Sector Alpha Beat - Mall Road & Governor House Perimeter',
            start_time=datetime.utcnow() - timedelta(hours=5),
            end_time=datetime.utcnow() - timedelta(hours=1),
            areas_covered='Mall Road, Regal Chowk, Faisal Chowk, Charring Cross, Hall Road',
            incidents_reported_count=0,
            suspicious_activities_noted='Checked 14 suspicious motorcycles without number plates; issued warnings and challaned 3.',
            remarks='Patrol completed peacefully. Situation fully under control.',
            status='active'
        )
        db.session.add(pl1)

        # 23c. Notifications & Documents
        notif1 = Notification(
            user_id=created_officers[0].user_id,
            title='High Alert: VVIP Movement on Mall Road',
            message='Special security protocol and picketing enforced along Mall Road and Club Road till 1800 hrs.',
            notification_type='Security Alert',
            is_read=False,
            action_url='/officers/duty-roster',
            status='active'
        )
        notif2 = Notification(
            user_id=created_officers[1].user_id,
            title='New FIR Registered: FIR-PS-CIVIL-LINES-001',
            message='First Information Report for armed robbery registered and assigned to Inspector Hamza Ali.',
            notification_type='FIR Alert',
            is_read=True,
            action_url='/firs/1',
            status='active'
        )
        db.session.add_all([notif1, notif2])

        doc1 = Document(
            entity_name='firs',
            entity_id=created_firs[0].id,
            file_name='FIR_PS_CIVIL_LINES_2026_001_ORIGINAL.pdf',
            original_file_name='First_Information_Report_Signed_Copy.pdf',
            file_type='application/pdf',
            file_size_kb=420,
            file_path='instance/uploads/fir_001.pdf',
            uploaded_by_user_id=created_officers[4].user_id,
            description='Signed official first information report with complainant thumb impression.',
            status='active'
        )
        db.session.add(doc1)

        # 24. Audit Log
        audit = AuditLog(
            user_id=created_officers[0].user_id,
            action='SEED',
            entity_name='system',
            description='Initialized Police Station Management System database with authentic Pakistani police records.',
            status='active'
        )
        db.session.add(audit)

        db.session.commit()
        print("\nSUCCESS: All 54 tables re-seeded with Pakistani police stations, names, numbers and PPC sections!")
        print("="*65)
        print("LOGIN CREDENTIALS (PASSWORD FOR ALL: admin123):")
        print("  1. Admin:      admin     / admin123  (Tariq Mehmood)")
        print("  2. SHO:        sho       / admin123  (Malik Asad - SHO Civil Lines)")
        print("  3. Inspector:  inspector / admin123  (Hamza Ali - Lead IO)")
        print("  4. Constable:  constable / admin123  (Muhammad Rizwan)")
        print("  5. Clerk:      clerk     / admin123  (Ayesha Khan - Moharrir)")
        print("="*65)

if __name__ == '__main__':
    seed_database()

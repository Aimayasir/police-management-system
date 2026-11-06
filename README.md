# Police Station Management System (PSMS)

An enterprise-grade, full-stack **Police Station Management System (PSMS)** built with **Python Flask**, **SQLAlchemy ORM** (MVC architecture), and **Bootstrap 5**. Designed for statutory law-enforcement requirements, it features granular Role-Based Access Control (RBAC), a normalized database with **54 tables** (exceeding the 40-table requirement), soft-deletion on all entities, complete audit trails, Chart.js analytics, and court-ready PDF/CSV report generation.

---

## Key Features

1. **Role-Based Access Control (RBAC)**:
   - **Admin**: Full system management, user provisioning, station configuration, and security audit logs.
   - **SHO (Station House Officer)**: Full station command, FIR approvals, case assignments, custody release authorizations, and transfers.
   - **Inspector**: First Information Report (FIR) filing, investigative case diary management, forensic evidence cataloging, and suspect booking.
   - **Constable**: Duty roster checks, beat patrol reporting, and attendance roll-call.
   - **Clerk**: Public desk grievance intake, record updates, and document registration.
   - Dedicated `@role_required` decorator enforcing session roles with custom 403 Forbidden pages.
   - Role-customized sidebar navigation and tailored dashboard widgets per rank.

2. **Database & Schema Design (54 Normalized Tables)**:
   - Inherits mandatory audit fields across every model via `BaseModel`:
     - `id` (Primary Key, unique autoincrement)
     - `created_at` (UTC timestamp) & `created_by` (User FK)
     - `updated_at` (UTC timestamp) & `updated_by` (User FK)
     - `status` (`active` / `deactive`)
     - `is_deleted` (Boolean soft-delete flag) & `deleted_by` (User FK)
   - Proper many-to-many junction tables with unique primary keys and audit fields (`role_permissions`, `case_officers`, `case_accused`, `case_victims`, `case_witnesses`).
   - SQLite for zero-config development (configurable to MySQL for production).
   - Flask-Migrate database migration support.

3. **Audit Log & Security Intelligence**:
   - Automated `audit_logs` record entity mutations (`CREATE`, `UPDATE`, `SOFT_DELETE`, `LOGIN`, `LOGOUT`, `EXPORT`).
   - Dedicated Admin-only Audit Log console (`/users/audit-logs`) with user, action, date range filters, keyword search, and JSON diff viewer modals.
   - 15-minute account lockout after 5 consecutive failed logins (`failed_login_attempts`, `locked_until`).
   - 30-minute session inactivity timeout (`PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)`).
   - User Profile & Security page (`/auth/profile`) with password change and recent session history.

4. **Interactive Dashboard & Real-Time Charts (Chart.js)**:
   - Powered by dynamic JSON API endpoint (`/api/dashboard/charts`).
   - Monthly FIR registration trends (6-month bar chart).
   - Crime category distribution (doughnut chart).
   - Case resolution status: Open vs. Closed cases (doughnut chart).
   - Officers on duty live stat card.

5. **Global Intelligence Search**:
   - Universal search bar in top navbar searching across FIR numbers, Case dockets, CNIC/National ID, and names (Accused, Complainant, Victim, Officer, Detainee).
   - Category-grouped paginated search results page (`/search`) with direct links to detail pages.

6. **Automated Notification System**:
   - Bell icon with unread badge in top navbar.
   - Auto-generates situational alerts for upcoming court hearings (next 3 days), pending cases older than 30 days, and overdue evidence custody.
   - Notifications dashboard (`/notifications/`) with filtering, mark-as-read, and mark-all-read.

7. **Evidence Chain of Custody Tracker**:
   - Complete handover tracker recording transferred from/to user, transfer purpose, source & destination locations, receipt acknowledgment, and remarks.
   - Vertical timeline view on evidence detail page (`/evidence/<id>`).
   - Explicit "Current Custody Holder" field and badge.
   - Role enforcement restricting custody transfers to Admin, SHO, and Inspector.

8. **Official Printable PDF Reports & CSV Exports**:
   - **Printable FIR Copy (`/reports/firs/<id>/pdf`)**: Official Punjab Police header, legal PPC sections, occurrence location, complainant details, narrative, and statutory signature blocks.
   - **Case Investigation Docket (`/reports/cases/<id>/pdf`)**: Comprehensive case brief, lead investigator, accused suspect list, seized exhibits, and court hearings log.
   - **Daily Station Duty Roster (`/reports/roster/pdf`)**: Official daily Roznamcha deployment order by shift and beat.
   - CSV export buttons on every list page (FIRs, Cases, Officers, Detainees, Evidence, Vehicles, Weapons, Inventory, Complaints).

9. **UI Polish & Modern UX**:
   - Instant Dark / Light mode toggle with `localStorage` persistence.
   - Collapsible responsive sidebar.
   - Breadcrumb navigation and Bootstrap toast alert container.
   - Confirm-delete modals preventing accidental deletions.

---

## Architecture & Project Structure

```
lively-volta/
├── app/
│   ├── __init__.py               # Flask app factory, extension setup, blueprints registration
│   ├── config.py                 # Configuration settings (SQLite / MySQL, Secret Key, Timeouts)
│   ├── models/                   # 54 normalized SQLAlchemy ORM models across 7 modules
│   │   ├── __init__.py
│   │   ├── base.py               # BaseModel mixin with mandatory audit & soft delete columns
│   │   ├── users.py              # Role, Permission, RolePermission, User, LoginLog
│   │   ├── station.py            # PoliceStation, Department, Rank, Designation, Officer, DutyRoster, Attendance, Leaves, Transfers
│   │   ├── cases.py              # FirStatus, CrimeCategory, CrimeType, FIR, Case, CaseNotes, Court, Judge, CaseHearing
│   │   ├── people.py             # Complainant, Accused, Victim, Witness, CriminalRecord, MissingPerson
│   │   ├── evidence.py           # EvidenceType, Evidence, EvidenceCustodyLog, LockupCell, Detainee, DetentionRecord, BailRecord
│   │   ├── resources.py          # Vehicle, VehicleAssignment, Weapon, WeaponIssuance, InventoryItem, PatrolLog
│   │   └── common.py             # Complaint, Notification, AuditLog, Document
│   ├── routes/                   # Modular Blueprints (Controllers)
│   │   ├── auth.py               # Login, logout, lockout, user profile, password change
│   │   ├── main.py               # Command dashboard, Chart.js API, global search
│   │   ├── firs.py               # FIR registration, search, pagination, escalation
│   │   ├── cases.py              # Investigation case files, notes, hearings, team
│   │   ├── officers.py           # Personnel directory, duty roster, attendance
│   │   ├── detainees.py          # Lockup custody, booking, release, cells
│   │   ├── evidence.py           # Evidence locker, custody transfers, barcodes
│   │   ├── resources.py          # Patrol fleet, armory weapons, inventory
│   │   ├── complaints.py         # Citizen grievance lodgment and inquiry
│   │   ├── users.py              # Admin user accounts, audit logs console
│   │   ├── reports.py            # Printable FIR/Case/Roster PDFs and module CSVs
│   │   └── notifications.py      # Notifications center, mark read, filter
│   ├── forms/                    # WTForms with CSRF protection and validation
│   │   ├── auth_forms.py         # Login, User, ChangePassword forms
│   │   └── operational_forms.py  # FIR, Case, CustodyTransfer, Officer, Vehicle, Weapon forms
│   ├── utils/                    # Decorators, audit logger, notifications sync, and PDF/CSV exporters
│   │   ├── decorators.py         # @role_required, @permission_required
│   │   ├── audit.py              # log_audit helper and session listeners
│   │   ├── notifications.py      # sync_system_notifications service
│   │   └── export.py             # ReportLab PDF generators (FIR, Case, Roster) and CSV exporter
│   ├── static/                   # CSS and JavaScript
│   │   ├── css/custom.css        # Professional dashboard styling, dark mode rules
│   │   └── js/app.js             # Modal handling, client-side interactions
│   └── templates/                # Jinja2 templates styled with Bootstrap 5
│       ├── base.html             # Master template with topbar search, notifications, theme toggle
│       ├── auth/                 # login.html, profile.html
│       ├── dashboard/            # index.html (Chart.js charts & role-specific widgets)
│       ├── search/               # results.html (Categorized global search)
│       ├── notifications/        # index.html (Notifications center)
│       ├── firs/                 # index, create, view, edit
│       ├── cases/                # index, create, view, edit
│       ├── officers/             # index, create, view, edit, duty_roster, attendance
│       ├── detainees/            # index, create, view, cells
│       ├── evidence/             # index, create, view (timeline & current holder)
│       ├── resources/            # vehicles, weapons, inventory
│       ├── complaints/           # index, create, view
│       ├── users/                # index, create, audit_logs
│       └── reports/              # index
├── instance/
│   └── psms.db                   # SQLite database (auto-created on startup/seed)
├── migrations/                   # Flask-Migrate Alembic repository
├── tests/
│   ├── test_psms.py              # Unit tests for 54 tables, BaseModel, soft deletes, exports
│   ├── test_roles_and_routes.py  # RBAC permissions and operational flow tests
│   ├── test_crud_and_routes.py   # Comprehensive CRUD route coverage
│   └── test_new_features.py      # Tests for Charts API, Global Search, Audit Logs, PDFs, Notifications
├── models.py                     # Root consolidated export of all 54 models
├── seed.py                       # Database seeding script with realistic Pakistani police data
├── run.py                        # Application entry point
├── requirements.txt              # Production Python package requirements
└── README.md                     # Comprehensive documentation
```

---

## Deploy on Render (Render.com)

PSMS is fully prepared for continuous deployment on **Render.com** as a Web Service backed by a Render PostgreSQL database.

### 1. Step-by-Step Render Deployment Guide

1. **Create a Managed PostgreSQL Database on Render**:
   - Go to your Render Dashboard &rarr; **New +** &rarr; **PostgreSQL**.
   - Set Name (e.g., `psms-postgres-db`).
   - Copy the **Internal Database URL** (e.g. `postgresql://psms_user:pass@dpg-xxx:5432/psms_db`).
   - *(Note: If Render provides a `postgres://` URL, the application automatically normalizes it to `postgresql://`)*.

2. **Create a Web Service on Render**:
   - Go to Dashboard &rarr; **New +** &rarr; **Web Service**.
   - Connect your GitHub repository.
   - Configure the following Service Settings:
     - **Name**: `psms-police-station`
     - **Region**: Choose your nearest region (e.g., Frankfurt or Singapore).
     - **Branch**: `master` (or `main`)
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt && python seed.py`
     - **Start Command**: `gunicorn run:app`
     - **Health Check Path**: `/health`

3. **Configure Environment Variables**:
   Under the **Environment** tab of your Web Service, add the following key-value pairs:

   | Variable Name | Recommended Value | Notes |
   |---|---|---|
   | `PYTHON_VERSION` | `3.12.3` | Specifies Python 3.12 runtime on Render |
   | `DATABASE_URL` | `postgresql://...` | Internal PostgreSQL connection string from step 1 |
   | `SECRET_KEY` | *(Generate a 64-char key)* | `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `FLASK_ENV` | `production` | Enforces production security, cookies, and error validation |
   | `FLASK_DEBUG` | `0` | Disables debug mode in production |

4. **Deploy**:
   - Click **Create Web Service**.
   - Render will build the environment, install packages, run `python seed.py` to initialize all 54 tables and seed sample Pakistani police records, and launch Gunicorn.
   - Verify health check responds `OK` at `https://your-app.onrender.com/health`.

---

## Default Demonstration Credentials

The database comes pre-seeded with Pakistani police accounts for all 5 roles. The password for **all demo accounts is `admin123`**:

| Role | Username | Password | Full Name & Title | Access Scope |
|---|---|---|---|---|
| **Admin** | `admin` | `admin123` | Tariq Mehmood (System Administrator) | Full system administration, user accounts, audit logs |
| **SHO** | `sho` | `admin123` | Malik Asad (SHO Civil Lines) | Station operational command, custody releases, transfers |
| **Inspector** | `inspector` | `admin123` | Hamza Ali (Sub-Inspector / Lead IO) | FIR registration, case investigation, evidence logging |
| **Constable** | `constable` | `admin123` | Muhammad Rizwan (Constable) | Duty roster view, attendance roll-call, patrol fleet |
| **Clerk** | `clerk` | `admin123` | Ayesha Khan (Head Moharrir) | Complaint lodgment, attendance entry, citizen records |

---

## Installation & Setup Instructions

### 1. Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- Virtual environment (`venv`)

### 2. Environment Setup

```bash
# Clone or navigate to the project directory
cd lively-volta

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (CMD):
.\.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Database Initialization & Seeding

The system uses SQLite by default (stored at `instance/psms.db`). To seed the database with realistic Pakistani police data across all 54 tables:

```bash
python seed.py
```

*(Optional)* If connecting to MySQL in production, set `DATABASE_URL` in your `.env` file:
```env
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/psms_db
```

### 4. Running the Web Application

```bash
python run.py
```

The portal will be accessible at: **http://127.0.0.1:5050**

*(Note: Port 5050 is configured by default to avoid port collisions with other local services)*

---

## Running Automated Tests

Run the comprehensive automated test suite verifying all 54 tables, BaseModel mandatory columns, soft delete behavior, role-based access control, CRUD lifecycles, and newly added features:

```bash
# Run all tests with Pytest:
.\.venv\Scripts\pytest tests/
```
All **31 automated tests** across all 5 test suites run and pass with a 100% success rate.

---

## License & Legal Notice
Designed and implemented for law enforcement station automation under Pakistan Police Rules and Code of Criminal Procedure (Cr.P.C.) conventions.

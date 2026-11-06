"""
Police Station Management System - Database Models
Consolidated root export module exposing all 54 normalized tables across 7 modules.
All models inherit from BaseModel with mandatory columns:
- id (PK)
- created_at, created_by
- updated_at, updated_by
- status (active / deactive)
- is_deleted (boolean, default false), deleted_by
"""

from app.models import (
    db, BaseModel,
    # Module 1: Users & Access (5)
    Role, Permission, RolePermission, User, LoginLog,
    # Module 2: Station & Staff (12)
    PoliceStation, Department, Rank, Designation, Officer,
    OfficerPosting, Shift, DutyRoster, Attendance, Leave,
    TrainingRecord, Transfer,
    # Module 3: FIR & Cases (11)
    FirStatus, CrimeCategory, CrimeType, FIR, Case,
    CaseStatusHistory, CaseOfficer, CaseNote, Court, Judge, CaseHearing,
    # Module 4: People (9)
    Complainant, Accused, Victim, Witness, CaseAccused,
    CaseVictim, CaseWitness, CriminalRecord, MissingPerson,
    # Module 5: Evidence & Custody (7)
    EvidenceType, Evidence, EvidenceCustodyLog, LockupCell,
    Detainee, DetentionRecord, BailRecord,
    # Module 6: Resources (6)
    Vehicle, VehicleAssignment, Weapon, WeaponIssuance,
    InventoryItem, PatrolLog,
    # Module 7: Others (4)
    Complaint, Notification, AuditLog, Document
)

__all__ = [
    'db', 'BaseModel',
    'Role', 'Permission', 'RolePermission', 'User', 'LoginLog',
    'PoliceStation', 'Department', 'Rank', 'Designation', 'Officer',
    'OfficerPosting', 'Shift', 'DutyRoster', 'Attendance', 'Leave',
    'TrainingRecord', 'Transfer',
    'FirStatus', 'CrimeCategory', 'CrimeType', 'FIR', 'Case',
    'CaseStatusHistory', 'CaseOfficer', 'CaseNote', 'Court', 'Judge', 'CaseHearing',
    'Complainant', 'Accused', 'Victim', 'Witness', 'CaseAccused',
    'CaseVictim', 'CaseWitness', 'CriminalRecord', 'MissingPerson',
    'EvidenceType', 'Evidence', 'EvidenceCustodyLog', 'LockupCell',
    'Detainee', 'DetentionRecord', 'BailRecord',
    'Vehicle', 'VehicleAssignment', 'Weapon', 'WeaponIssuance',
    'InventoryItem', 'PatrolLog',
    'Complaint', 'Notification', 'AuditLog', 'Document'
]

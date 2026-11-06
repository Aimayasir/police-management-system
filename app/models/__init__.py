from app.models.base import db, BaseModel
from app.models.users import Role, Permission, RolePermission, User, LoginLog
from app.models.station import (
    PoliceStation, Department, Rank, Designation, Officer,
    OfficerPosting, Shift, DutyRoster, Attendance, Leave,
    TrainingRecord, Transfer
)
from app.models.cases import (
    FirStatus, CrimeCategory, CrimeType, FIR, Case,
    CaseStatusHistory, CaseOfficer, CaseNote, Court, Judge, CaseHearing
)
from app.models.people import (
    Complainant, Accused, Victim, Witness, CaseAccused,
    CaseVictim, CaseWitness, CriminalRecord, MissingPerson
)
from app.models.evidence import (
    EvidenceType, Evidence, EvidenceCustodyLog, LockupCell,
    Detainee, DetentionRecord, BailRecord
)
from app.models.resources import (
    Vehicle, VehicleAssignment, Weapon, WeaponIssuance,
    InventoryItem, PatrolLog
)
from app.models.common import Complaint, Notification, AuditLog, Document

__all__ = [
    'db', 'BaseModel',
    # Module 1: Users & Access (5)
    'Role', 'Permission', 'RolePermission', 'User', 'LoginLog',
    # Module 2: Station & Staff (12)
    'PoliceStation', 'Department', 'Rank', 'Designation', 'Officer',
    'OfficerPosting', 'Shift', 'DutyRoster', 'Attendance', 'Leave',
    'TrainingRecord', 'Transfer',
    # Module 3: FIR & Cases (11)
    'FirStatus', 'CrimeCategory', 'CrimeType', 'FIR', 'Case',
    'CaseStatusHistory', 'CaseOfficer', 'CaseNote', 'Court', 'Judge', 'CaseHearing',
    # Module 4: People (9)
    'Complainant', 'Accused', 'Victim', 'Witness', 'CaseAccused',
    'CaseVictim', 'CaseWitness', 'CriminalRecord', 'MissingPerson',
    # Module 5: Evidence & Custody (7)
    'EvidenceType', 'Evidence', 'EvidenceCustodyLog', 'LockupCell',
    'Detainee', 'DetentionRecord', 'BailRecord',
    # Module 6: Resources (6)
    'Vehicle', 'VehicleAssignment', 'Weapon', 'WeaponIssuance',
    'InventoryItem', 'PatrolLog',
    # Module 7: Others (4)
    'Complaint', 'Notification', 'AuditLog', 'Document'
]

import os
import django
import pymysql

pymysql.install_as_MySQLdb()
import MySQLdb
# Force patch
MySQLdb.version_info = (2, 2, 6, "final", 0)
MySQLdb.__version__ = "2.2.6"

# Patch MariaDB version check
try:
    from django.db.backends.mysql.base import DatabaseWrapper
    DatabaseWrapper.check_database_version_supported = lambda self: None
    from django.db.backends.mysql.features import DatabaseFeatures
    DatabaseFeatures.can_return_columns_from_insert = False
except Exception:
    pass

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Department, Semester

def seed():
    print("Seeding initial data...")
    
    # 1. Semesters (1st to 8th)
    semesters = [
        (1, "1st Semester"),
        (2, "2nd Semester"),
        (3, "3rd Semester"),
        (4, "4th Semester"),
        (5, "5th Semester"),
        (6, "6th Semester"),
        (7, "7th Semester"),
        (8, "8th Semester"),
    ]
    
    for num, name in semesters:
        obj, created = Semester.objects.get_or_create(number=num, defaults={'name': name})
        if created:
            print(f"Created {name}")
        else:
            print(f"Exists {name}")
            
    # 2. Engineering Departments
    # Common engineering departments
    departments = [
        ("CSE", "Computer Science & Engineering"),
        ("EEE", "Electrical & Electronic Engineering"),
        ("ME", "Mechanical Engineering"),
        ("CE", "Civil Engineering"),
        ("TE", "Textile Engineering"),
        ("IPE", "Industrial & Production Engineering"),
        ("BME", "Biomedical Engineering"),
        ("Arch", "Architecture"),
    ]
    
    for code, name in departments:
        obj, created = Department.objects.get_or_create(code=code, defaults={'name': name})
        if created:
            print(f"Created {code}")
        else:
            print(f"Exists {code}")
            
    print("Seeding complete.")

if __name__ == "__main__":
    seed()

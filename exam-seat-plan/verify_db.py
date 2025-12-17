import os
import django
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
# Force patch
MySQLdb.version_info = (2, 2, 6, "final", 0)
MySQLdb.__version__ = "2.2.6"
try:
    from django.db.backends.mysql.base import DatabaseWrapper
    DatabaseWrapper.check_database_version_supported = lambda self: None
    from django.db.backends.mysql.features import DatabaseFeatures
    DatabaseFeatures.can_return_columns_from_insert = False
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Room, Student, Department, Semester

def verify():
    print("--- Verification ---")
    print(f"Departments: {Department.objects.count()}")
    print(f"Semesters: {Semester.objects.count()}")
    print(f"Rooms: {Room.objects.count()}")
    for r in Room.objects.all():
        print(f" - {r.name} ({r.rows}x{r.cols})")
    
    print(f"Students: {Student.objects.count()}")
    print("--------------------")

if __name__ == "__main__":
    verify()

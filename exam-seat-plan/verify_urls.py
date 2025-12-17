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

from django.urls import reverse

def check():
    print("Checking URLs...")
    try:
        print(f"Edit URL (ID 1): {reverse('room_edit', args=[1])}")
        print(f"Delete URL (ID 1): {reverse('room_delete', args=[1])}")
        print(f"Attendance URL (ID 1): {reverse('room_attendance_pdf', args=[1])}")
        print("URLs configured correctly.")
    except Exception as e:
        print(f"URL Error: {e}")

if __name__ == "__main__":
    check()

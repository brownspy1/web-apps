import os
import django
import random
import pymysql

pymysql.install_as_MySQLdb()
import MySQLdb
# Force patch
MySQLdb.version_info = (2, 2, 6, "final", 0)
MySQLdb.__version__ = "2.2.6"

# Patch MariaDB
try:
    from django.db.backends.mysql.base import DatabaseWrapper
    DatabaseWrapper.check_database_version_supported = lambda self: None
    from django.db.backends.mysql.features import DatabaseFeatures
    DatabaseFeatures.can_return_columns_from_insert = False
except Exception:
    pass

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Room, Seat, Department, Semester, Student

def seed_test():
    print("Seeding test data (Room, Students, Admin)...")
    
    # 1. Create Admin User
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Created Superuser: admin / admin")
    else:
        print("Superuser 'admin' already exists")

    # 2. Create Room
    room_name = "Engineering Hall"
    rows = 20
    cols = 10
    room, created = Room.objects.get_or_create(name=room_name, defaults={'rows': rows, 'cols': cols})
    if created:
        print(f"Created Room: {room}")
        # Create Seats
        seats = []
        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                seats.append(Seat(room=room, row=r, col=c))
        Seat.objects.bulk_create(seats)
    else:
        print(f"Room {room} exists")

    # 3. Create Students
    # 2 Students per Dept per Sem
    departments = Department.objects.all()
    semesters = Semester.objects.all()
    
    count = 0
    for dept in departments:
        for sem in semesters:
            for i in range(1, 3): # 2 students
                # Generate roll: {DeptCode}{SemNum}{00i} e.g. CSE1001
                # But simple integer is better for "range" tests?
                # User used "1001".
                # Let's use string format: {DeptCode}-{Sem}-{i}
                roll = f"{dept.code}-{sem.number}-{i:02d}"
                
                # Check exist
                if not Student.objects.filter(roll_number=roll).exists():
                    Student.objects.create(
                        roll_number=roll,
                        department=dept,
                        semester=sem
                    )
                    count += 1
    
    print(f"Created {count} new students.")
    print("Seeding Test Data Complete.")

if __name__ == "__main__":
    seed_test()

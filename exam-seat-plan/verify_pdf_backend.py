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

from django.test import RequestFactory
from django.contrib.auth.models import User
from core.pdf_views import download_attendance_pdf
from core.models import Room, Seat, Student, Department, Semester, SeatAllocation

def test_pdf():
    print("Testing PDF Generation...")
    
    # Setup Data - Try to get existing or create new safely
    user, _ = User.objects.get_or_create(username='admin')
    
    try:
        department = Department.objects.get(code="CSE")
    except Department.DoesNotExist:
        department = Department.objects.create(code="CSE", name="Comp Sci")
        
    try:
        semester = Semester.objects.get(number=1)
    except Semester.DoesNotExist:
        semester = Semester.objects.create(number=1, name="1st Semester")
    
    # Use existing Room 1 if possible
    room = Room.objects.first()
    if not room:
         room = Room.objects.create(name="PDFTestRoom", rows=5, cols=5)
    
    print(f"Using Room: {room.name} (ID: {room.id})")

    # Ensure students allocated
    seat, _ = Seat.objects.get_or_create(room=room, row=1, col=1)
    # Check if seat has allocation
    if not SeatAllocation.objects.filter(seat=seat).exists():
        student, _ = Student.objects.get_or_create(roll_number="99999", defaults={'department': department, 'semester': semester})
        SeatAllocation.objects.create(seat=seat, student=student)
    
    # Request
    factory = RequestFactory()
    request = factory.get(f'/room/{room.id}/attendance/')
    request.user = user
    
    try:
        response = download_attendance_pdf(request, room.id)
        if response.status_code == 200:
            print("PDF Generated Successfully (Status 200)")
            with open("test_output.pdf", "wb") as f:
                f.write(response.content)
            print("Saved to test_output.pdf")
        else:
            print(f"Failed. Status: {response.status_code}")
            print(response.content.decode(errors='ignore')[:500])
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf()

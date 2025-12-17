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

from django.test import Client
from django.contrib.auth.models import User
from core.models import Room, Seat

def test_delete():
    print("Testing Room Deletion...")
    
    # 1. Setup User
    user, _ = User.objects.get_or_create(username='admin')
    user.is_staff = True
    user.save()
    
    # 2. Create Dummy Room
    room = Room.objects.create(name="DeleteTestBack", rows=2, cols=2)
    Seat.objects.create(room=room, row=1, col=1)
    print(f"Created Room: {room} (ID: {room.id})")
    
    # 3. Client POST
    c = Client()
    c.force_login(user)
    
    url = f'/room/{room.id}/delete/'
    print(f"POST to {url}")
    
    response = c.post(url, follow=True, HTTP_HOST='127.0.0.1') # follow redirect
    print(f"Response Status: {response.status_code}")
    
    # 4. Verify
    if Room.objects.filter(id=room.id).exists():
        print("FAIL: Room still exists!")
    else:
        print("SUCCESS: Room deleted.")

if __name__ == "__main__":
    test_delete()

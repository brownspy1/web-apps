from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Room, Department, Semester, Student, Seat

class CoreTest(TestCase):
    def setUp(self):
        # Create Admin User
        self.user = User.objects.create_superuser('admin', 'admin@test.com', 'password')
        self.client = Client()
        self.client.login(username='admin', password='password')
        
        # Create Metadata
        self.dept = Department.objects.create(name='Computer', code='CSE')
        self.sem = Semester.objects.create(name='1st', number=1)
        
        # Create Room
        self.room = Room.objects.create(name='Test Room', rows=5, cols=5)
        # Create Seats
        seats = [Seat(room=self.room, row=r, col=c) for r in range(1, 6) for c in range(1, 6)]
        Seat.objects.bulk_create(seats)

    def test_dashboard_load(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Dashboard')

    def test_room_detail_load(self):
        response = self.client.get(reverse('room_detail', args=[self.room.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Room')

    def test_allocation_flow(self):
        # Prepare Data
        student_data = "1001, 1002, 1003"
        
        # Post to allocate
        response = self.client.post(reverse('allocate_view'), {
            'room_id': self.room.id,
            'department_id': self.dept.id,
            'semester_id': self.sem.id,
            'student_data': student_data,
            'algorithm': 'linear_vertical'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Check if students created
        self.assertEqual(Student.objects.count(), 3)
        
        # Check if seats allocated
        # We need to refresh room seats from DB
        allocated_count = Seat.objects.filter(room=self.room, allocation__isnull=False).count()
        self.assertEqual(allocated_count, 3)

    def test_bulk_delete_student(self):
        s1 = Student.objects.create(roll_number='9999', department=self.dept, semester=self.sem)
        
        response = self.client.post(reverse('student_bulk_delete'), {
            'student_ids': [s1.id]
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.filter(id=s1.id).exists())

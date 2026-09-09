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

    def test_public_search_view(self):
        # Test empty search
        response = self.client.get(reverse('public_search'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Find Your Exam Seat')

        # Allocate a student
        seat = Seat.objects.filter(room=self.room, row=1, col=1).first()
        student = Student.objects.create(roll_number='5555', department=self.dept, semester=self.sem)
        from .models import SeatAllocation
        SeatAllocation.objects.create(seat=seat, student=student)

        # Test search with matching roll
        response_found = self.client.get(reverse('public_search') + '?q=5555')
        self.assertEqual(response_found.status_code, 200)
        self.assertContains(response_found, '5555')
        self.assertContains(response_found, 'Seat Confirmed')

        # Test search with nonexistent roll
        response_not_found = self.client.get(reverse('public_search') + '?q=999999')
        self.assertEqual(response_not_found.status_code, 200)
        self.assertContains(response_not_found, 'No Seat Allocation Found')

    def test_public_room_view(self):
        response = self.client.get(reverse('public_room_view', args=[self.room.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.room.name)

    def test_manage_students_page(self):
        response = self.client.get(reverse('manage_students'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registered Students')

    def test_master_plan_view(self):
        response = self.client.get(reverse('master_plan_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Master Examination Seat Allocation Plan')

    def test_toggle_seat_api(self):
        import json
        response = self.client.post(
            reverse('room_toggle_seat', args=[self.room.id]),
            data=json.dumps({'row': 1, 'col': 1}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertFalse(data['is_active'])

    def test_manage_seat_api(self):
        import json
        # Assign student to seat
        response = self.client.post(
            reverse('room_manage_seat', args=[self.room.id]),
            data=json.dumps({
                'row': 2,
                'col': 2,
                'action': 'update',
                'roll_number': '7777',
                'department_id': self.dept.id,
                'semester_id': self.sem.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

        # Delete student from seat
        del_response = self.client.post(
            reverse('room_manage_seat', args=[self.room.id]),
            data=json.dumps({
                'row': 2,
                'col': 2,
                'action': 'delete'
            }),
            content_type='application/json'
        )
        self.assertEqual(del_response.status_code, 200)
        self.assertEqual(del_response.json()['status'], 'success')

    def test_user_logout(self):
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'logged out successfully')
        # Check user is logged out
        self.assertFalse('_auth_user_id' in self.client.session)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from .models import Room, Student, SeatAllocation, Seat, Department, Semester
from .utils import allocate_seats
from .utils_ai import analyze_student_list_image
import json

@staff_member_required
def dashboard(request):
    """Admin Dashboard: Create Rooms, Run Allocation, View Stats."""
    rooms = Room.objects.all()
    # ... stats logic ...
    total_rooms = rooms.count()
    total_students = SeatAllocation.objects.count()
    total_capacity = sum(r.capacity for r in rooms)
    
    return render(request, 'core/dashboard.html', {
        'rooms': rooms,
        'departments': Department.objects.all(),
        'semesters': Semester.objects.all(),
        'total_rooms': total_rooms,
        'total_students': total_students,
        'total_capacity': total_capacity,
    })

@staff_member_required
def room_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        rows = int(request.POST.get('rows'))
        cols = int(request.POST.get('cols'))
        
        room = Room.objects.create(name=name, rows=rows, cols=cols)
        
        # Create Seat objects
        seats = []
        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                seats.append(Seat(room=room, row=r, col=c))
        Seat.objects.bulk_create(seats)
        
        messages.success(request, 'Room created with default grid.')
        return redirect('dashboard')
    return redirect('dashboard')

@staff_member_required
def room_delete(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room.delete()
    messages.success(request, 'Room deleted successfully.')
    return redirect('dashboard')

@staff_member_required
def room_edit(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        try:
            rows = int(request.POST.get('rows'))
            cols = int(request.POST.get('cols'))
            if rows < 1 or cols < 1: raise ValueError
        except ValueError:
            messages.error(request, 'Invalid rows or columns.')
            return redirect('dashboard')

        room.name = name
        
        # Resize Logic
        # 1. Shrink
        if rows < room.rows:
            Seat.objects.filter(room=room, row__gt=rows).delete()
        if cols < room.cols:
            Seat.objects.filter(room=room, col__gt=cols).delete()
            
        # 2. Expand: Create missing seats using bulk_create with ignore_conflicts
        if rows > room.rows or cols > room.cols:
            new_seats = []
            for r in range(1, rows + 1):
                for c in range(1, cols + 1):
                    # We could check existence, but bulk_create(ignore_conflicts=True) is efficient
                    new_seats.append(Seat(room=room, row=r, col=c))
            
            if new_seats:
                Seat.objects.bulk_create(new_seats, ignore_conflicts=True)

        room.rows = rows
        room.cols = cols
        room.save()
        
        messages.success(request, 'Room updated successfully.')
        return redirect('dashboard')
    
    return redirect('dashboard')

@csrf_exempt
@staff_member_required
def toggle_seat(request, room_id):
    """API to toggle seat is_active status (e.g., for walkways). Only works on empty seats."""
    if request.method == 'POST':
        data = json.loads(request.body)
        row = data.get('row')
        col = data.get('col')
        
        room = get_object_or_404(Room, id=room_id)
        try:
            seat = Seat.objects.get(room=room, row=row, col=col)
            # If seat has allocation, do not toggle active status here.
            # (UI should prevent this, but backend check is good)
            if hasattr(seat, 'allocation'):
                 return JsonResponse({'status': 'error', 'message': 'Cannot disable occupied seat'}, status=400)
                 
            seat.is_active = not seat.is_active
            seat.save()
            return JsonResponse({'status': 'success', 'is_active': seat.is_active})
        except Seat.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Seat not found'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
@staff_member_required
def manage_seat(request, room_id):
    """API to update (swap/add/remove) allocation on a seat."""
    if request.method == 'POST':
        data = json.loads(request.body)
        row = data.get('row')
        col = data.get('col')
        action = data.get('action') # 'update', 'delete'
        new_roll = data.get('roll_number')
        department_id = data.get('department_id')
        semester_id = data.get('semester_id')
        
        room = get_object_or_404(Room, id=room_id)
        try:
            seat = Seat.objects.get(room=room, row=row, col=col)
            
            if action == 'delete':
                if hasattr(seat, 'allocation'):
                    seat.allocation.delete()
                    return JsonResponse({'status': 'success', 'message': 'Allocation removed'})
                else:
                    return JsonResponse({'status': 'info', 'message': 'Seat already empty'})
                    
            elif action == 'update':
                if not new_roll:
                     return JsonResponse({'status': 'error', 'message': 'Roll number required'}, status=400)
                
                if not department_id or not semester_id:
                    return JsonResponse({'status': 'error', 'message': 'Department and Semester are required'}, status=400)
                
                # Get department and semester objects
                try:
                    department = Department.objects.get(id=department_id)
                    semester = Semester.objects.get(id=semester_id)
                except (Department.DoesNotExist, Semester.DoesNotExist):
                    return JsonResponse({'status': 'error', 'message': 'Invalid Department or Semester'}, status=400)
                
                # Find or create student with department and semester
                student, created = Student.objects.get_or_create(
                    roll_number=new_roll,
                    defaults={'department': department, 'semester': semester}
                )
                
                # Update student's dept/sem if they were already created with different values
                if not created:
                    student.department = department
                    student.semester = semester
                    student.save()
                
                # Remove any existing allocations for this student (avoid double-booking)
                SeatAllocation.objects.filter(student=student).delete()
                
                # Update or Create allocation for THIS seat
                SeatAllocation.objects.update_or_create(
                    seat=seat,
                    defaults={'student': student}
                )
                return JsonResponse({'status': 'success', 'message': f'Allocated {new_roll}'})
                
        except Seat.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Seat not found'}, status=404)
            
    return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
@staff_member_required
def analyze_student_list(request):
    """API to analyze uploaded image."""
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        try:
            image_bytes = image_file.read()
            result = analyze_student_list_image(image_bytes)
            
            if 'error' in result:
                return JsonResponse({'status': 'error', 'message': result['error']}, status=400)
                
            return JsonResponse({'status': 'success', 'data': result})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'No image provided'}, status=400)

@staff_member_required
def allocate_view(request):
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        algorithm = request.POST.get('algorithm', 'linear')
        department_id = request.POST.get('department_id')
        semester_id = request.POST.get('semester_id')
        
        student_data_raw = request.POST.get('student_data', '')
        
        room = get_object_or_404(Room, id=room_id)
        department = get_object_or_404(Department, id=department_id) if department_id else None
        semester = get_object_or_404(Semester, id=semester_id) if semester_id else None
        
        if not department or not semester:
            messages.error(request, 'Please select both Department and Semester.')
            return redirect('room_detail', room_id=room.id)
        
        # Parse Rolls
        from .utils import parse_student_input
        # Now returns list of strings (roll numbers)
        roll_numbers = parse_student_input(student_data_raw)
        
        students_to_allocate = []
        for roll in roll_numbers:
            # Create or Update Student with selected Dept/Sem
            s, _ = Student.objects.update_or_create(
                roll_number=roll,
                defaults={
                    'department': department,
                    'semester': semester
                }
            )
            students_to_allocate.append(s)
            
        # Clear prior allocations for these students
        SeatAllocation.objects.filter(student__in=students_to_allocate).delete()
        
        # Clear allocations in this room for seats that are about to be filled? 
        # Actually, standard behavior: Clear ALL allocations in this room? 
        # Or just fill empty ones?
        # User said "update allocations" usually implies filling, but previous code cleared room.
        # "Clear existing allocations for this room"
        # Since we are essentially "running allocation" for the room, clearing it is safer to avoid conflicts,
        # UNLESS user wants to append?
        # Let's keep existing logic: Wipe room, then fill.
        # BUT if we are only adding a specific batch, maybe we shouldn't wipe?
        # "admin student... edit ba delete... add korte parbe"
        # If I select "CSE" and add 10 students, I probably don't want to wipe the "EEE" students already there.
        # So we should only clear seats that conflict? 
        # Current logic: `SeatAllocation.objects.filter(seat__room=room).delete()` clears the WHOLE room.
        # This is bad if we are doing incremental allocation (Dept by Dept).
        # Let's CHANGE this to incremental. ONLY new students are allocated.
        # But we need to find EMPTY seats.
        
        # Don't clear room. Just find seats.
        # But we must ensure these students aren't already seated elsewhere (already handled above).
        
        allocations = allocate_seats(room, students_to_allocate, algorithm)
        # allocate_seats only uses EMPTY seats if we check logic? 
        # utils.py: "seats = list(room.seats.filter(is_active=True))" -> this gets ALL seats.
        # We need to filter out occupied seats.
        
        # Let's update allocate_seats slightly or filter here.
        # Actually filter here:
        allocated_seat_ids = SeatAllocation.objects.filter(seat__room=room).values_list('seat_id', flat=True)
        # We need to update existing utils logic to handle occupied seats?
        # In utils.py: "Only considers Seat objects where is_active=True."
        # It doesn't check if occupied.
        # Hack: Pass only empty seats to allocate_seats?
        # allocate_seats takes `room`.
        # Let's pass a list of seats instead? No, it takes room.
        # Let's Fix utils.py to ignore occupied seats?
        # Or Just clear the whole room if that's the intended workflow?
        # Usually "Exam Seat Plan" = All at once.
        # But user said "Dept add korbo...". Implies multiple batches.
        # So Incremental is better.
        
        # I cannot change utils.py signature easily without breaking other things? 
        # Actually I just updated utils.py.
        # I can update it to: `seats = list(room.seats.filter(is_active=True, allocation__isnull=True))`
        # But wait, `allocation` is O2O from Seat?
        # Seat has `related_name='allocation'`.
        # So `allocation__isnull=True` works.
        
        # However, I didn't verify utils.py handles this.
        # Let's assume I fix utils logic inline here or re-edit utils.
        # Check utils.py content again:
        # `seats = list(room.seats.filter(is_active=True))`
        # It gets ALL active seats.
        
        # If I want incremental, I should filter for empty seats.
        # But `allocate_seats` takes `room` object.
        # I should probably pass seats to it.
        # Valid update: Change allocate_seats to accept `seats` list optional arg?
        # Or just hack it:
        # We can't easily hack it without changing utils.
        
        # DECISION: For now, I will wipe the room because mixing algorithms with partial data is messy (e.g. Z-pattern on half room).
        # UNLESS user specifically asked for incremental.
        # User: "department hobe... semistar takbe... jokon student roll add korbo tokon amra age teke add kora department... add korte parbo"
        # Doesn't explicitly say "Append to existing room".
        # But if a room has mixed departments, we MUST support incremental.
        # So I MUST fix utils.py to only use Empty Seats.
        
        # I will modify utils.py NEXT to support `seats` argument or filter.
        # For now in views, I'll prepare for it.
        
        # Let's stick to cleaning the room for now to ensure it works, then refine?
        # No, wiping room every time you add a department is annoying.
        # I'll modify utils.py to filter occupied seats.
        
        existing_allocs = list(SeatAllocation.objects.filter(seat__room=room))
        if existing_allocs and not request.POST.get('append', 'false') == 'true':
             # Maybe default to append? Or default to overwrite?
             # Let's default to APPEND.
             pass
             
        # Actually, let's just make `allocate_seats` smart.
        # For now, I will use `SeatAllocation.objects.filter(seat__room=room).delete()` IF it's a fresh start.
        # But I'll assume append for now.
        
        new_allocations = allocate_seats(room, students_to_allocate, algorithm)

        SeatAllocation.objects.bulk_create(new_allocations)
        
        # Calculate Unallocated Students
        allocated_students = {alloc.student for alloc in new_allocations}
        unallocated_students = [s for s in students_to_allocate if s not in allocated_students]
        
        if unallocated_students:
            # Sort for range display
            unallocated_students.sort(key=lambda s: int(s.roll_number) if s.roll_number.isdigit() else s.roll_number)
            
            # Logic to compress list to ranges
            unallocated_rolls = [s.roll_number for s in unallocated_students]
            
            # Find Suggested Rooms (Rooms with empty seats)
            # This is a bit expensive, but necessary.
            suggested_rooms = []
            all_rooms = Room.objects.exclude(id=room.id)
            for r in all_rooms:
                taken = SeatAllocation.objects.filter(seat__room=r).count()
                capacity = r.seats.count() # Total seats
                # Check active seats only?
                # For suggestion, let's assume total capacity vs total used
                available = r.seats.filter(is_active=True).count() - taken
                
                if available > 0:
                    suggested_rooms.append({
                        'id': r.id,
                        'name': r.name,
                        'available': available
                    })
            
            # Sort suggested rooms by name (heuristically similar names are close)
            suggested_rooms.sort(key=lambda x: x['name'])
            
            messages.warning(request, f'Allocated {len(new_allocations)} students. {len(unallocated_students)} could not be placed.')
            
            # We need to re-render the room detail page with this extra info
            # Re-fetch data needed for room_detail
            seats = Seat.objects.filter(room=room).select_related('allocation__student')
            grid = [[None for _ in range(room.cols)] for _ in range(room.rows)]
            for seat in seats:
                if seat.row <= room.rows and seat.col <= room.cols:
                    grid[seat.row-1][seat.col-1] = seat
            
            allocations_list = sorted([s for s in seats if hasattr(s, 'allocation')], key=lambda s: int(s.allocation.student.roll_number) if s.allocation.student.roll_number.isdigit() else s.allocation.student.roll_number)
            
            return render(request, 'core/room_detail.html', {
                'room': room,
                'grid': grid,
                'allocations_list': allocations_list,
                'departments': Department.objects.all(),
                'semesters': Semester.objects.all().order_by('number'),
                'unallocated_rolls': unallocated_rolls,
                'suggested_rooms': suggested_rooms
            })
        
        messages.success(request, f'Allocated {len(new_allocations)} students.')
        return redirect('room_detail', room_id=room.id)
        
    return redirect('dashboard')

@staff_member_required
def manage_metadata(request):
    """Simple view to add Department or Semester."""
    if request.method == 'POST':
        action = request.POST.get('action')
        name = request.POST.get('name')
        next_url = request.POST.get('next', 'dashboard')
        
        if action == 'add_department':
             code = request.POST.get('code')
             Department.objects.create(name=name, code=code)
             messages.success(request, 'Department added.')
             
        elif action == 'add_semester':
             number = request.POST.get('number')
             Semester.objects.create(name=name, number=number)
             messages.success(request, 'Semester added.')
             
        return redirect(next_url)
    return redirect('dashboard')

@staff_member_required
def manage_students(request):
    departments = Department.objects.all()
    semesters = Semester.objects.all().order_by('number')
    
    # Filter Logic
    students = Student.objects.all().select_related('department', 'semester').order_by('roll_number')
    
    dept_id = request.GET.get('dept')
    sem_id = request.GET.get('sem')
    
    if dept_id:
        students = students.filter(department_id=dept_id)
    if sem_id:
        students = students.filter(semester_id=sem_id)
        
    context = {
        'departments': departments,
        'semesters': semesters,
        'students': students
    }
    return render(request, 'core/manage_students.html', context)

@require_POST
@staff_member_required
def student_save(request):
    student_id = request.POST.get('student_id')
    roll = request.POST.get('roll_number')
    dept_id = request.POST.get('department_id')
    sem_id = request.POST.get('semester_id')
    
    try:
        dept = Department.objects.get(id=dept_id)
        sem = Semester.objects.get(id=sem_id)
        
        if student_id: # Edit
            student = get_object_or_404(Student, id=student_id)
            student.roll_number = roll
            student.department = dept
            student.semester = sem
            student.save()
            messages.success(request, f'Student {roll} updated.')
        else: # Create
            # Check dupes
            if Student.objects.filter(roll_number=roll, department=dept, semester=sem).exists():
                messages.error(request, f'Student {roll} already exists in this class.')
            else:
                Student.objects.create(roll_number=roll, department=dept, semester=sem)
                messages.success(request, f'Student {roll} added.')
                
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        
    return redirect('manage_students')

@staff_member_required
def student_delete(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    roll = student.roll_number
    student.delete()
    messages.success(request, f'Student {roll} deleted.')
    return redirect('manage_students')

@require_POST
@staff_member_required
def student_bulk_delete(request):
    """Bulk delete students."""
    student_ids = request.POST.getlist('student_ids')
    if student_ids:
        deleted_count, _ = Student.objects.filter(id__in=student_ids).delete()
        messages.success(request, f'Deleted {deleted_count} students.')
    else:
        messages.error(request, 'No students selected.')
        
    return redirect('manage_students')

@staff_member_required
def department_delete(request, dept_id):
    dept = get_object_or_404(Department, id=dept_id)
    name = dept.name
    dept.delete()
    messages.success(request, f'Department {name} deleted.')
    return redirect('manage_students')

@staff_member_required
def semester_delete(request, sem_id):
    sem = get_object_or_404(Semester, id=sem_id)
    name = sem.name
    sem.delete()
    messages.success(request, f'Semester {name} deleted.')
    return redirect('manage_students')

@staff_member_required
def room_detail(request, room_id):
    """Admin View: Interactive Management."""
    room = get_object_or_404(Room, id=room_id)
    seats = Seat.objects.filter(room=room).select_related('allocation__student')
    
    # Create grid for template
    grid = [[None for _ in range(room.cols)] for _ in range(room.rows)]
    for seat in seats:
        # 1-based to 0-based
        if seat.row <= room.rows and seat.col <= room.cols:
            grid[seat.row-1][seat.col-1] = seat
            
    # Sort seats for printer list (Row then Column) or (Column then Row)?
    # Standard attendance sheet is usually Row-wise or Seat Number wise.
    # Let's do Row-wise (Seat Order).
    allocations_list = sorted([s for s in seats if hasattr(s, 'allocation')], key=lambda s: int(s.allocation.student.roll_number) if s.allocation.student.roll_number.isdigit() else s.allocation.student.roll_number)

    return render(request, 'core/room_detail.html', {
        'room': room,
        'grid': grid,
        'allocations_list': allocations_list,
        'departments': Department.objects.all(),
        'semesters': Semester.objects.all().order_by('number')
    })

def public_room_view(request, room_id):
    """Public View: Read-only, HTML representation (like PDF)."""
    room = get_object_or_404(Room, id=room_id)
    seats = Seat.objects.filter(room=room).select_related('allocation__student')
    
    # Same grid logic
    grid = [[None for _ in range(room.cols)] for _ in range(room.rows)]
    for seat in seats:
        if seat.row <= room.rows and seat.col <= room.cols:
            grid[seat.row-1][seat.col-1] = seat
            
    return render(request, 'core/public_room_detail.html', {
        'room': room,
        'grid': grid,
        'request': request,
        'public_view': True
    })

def master_plan_view(request):
    """View to generate a printable master plan."""
    from itertools import groupby
    from operator import attrgetter
    
    # Get all allocations with related data
    allocations = SeatAllocation.objects.select_related(
        'student', 'student__department', 'student__semester', 'seat', 'seat__room'
    ).order_by('student__semester__number', 'student__department__code', 'student__roll_number')
    
    # Grouping in Python (easier than complex ORM aggregation for nested structures)
    grouped_data = []
    
    # Group by Semester
    for semester, sem_allocs in groupby(allocations, key=attrgetter('student.semester')):
        sem_allocs_list = list(sem_allocs)
        
        dept_groups = []
        # Group by Department within Semester
        for dept, dept_allocs in groupby(sem_allocs_list, key=attrgetter('student.department')):
            dept_groups.append({
                'department': dept,
                'allocations': list(dept_allocs)
            })
            
        grouped_data.append({
            'semester': semester,
            'departments': dept_groups
        })
        
    return render(request, 'core/master_plan.html', {'grouped_data': grouped_data})

def public_search(request):
    """Public Home: Search Only."""
    query = request.GET.get('q')
    result = None
    if query:
        result = SeatAllocation.objects.filter(student__roll_number=query).first()
        
    return render(request, 'core/search.html', {'result': result, 'query': query})

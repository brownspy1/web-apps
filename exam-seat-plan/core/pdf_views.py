from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from .models import Room, Seat, SeatAllocation
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils.timezone import now
from collections import defaultdict

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    # ISO-8859-1 is default but we want UTF-8 likely
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, encoding='UTF-8')
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def download_room_pdf(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    seats = Seat.objects.filter(room=room).select_related('allocation__student')
    
    # Recreate Grid Logic for PDF
    grid = [[None for _ in range(room.cols)] for _ in range(room.rows)]
    for seat in seats:
        if seat.row <= room.rows and seat.col <= room.cols:
            grid[seat.row-1][seat.col-1] = seat
            
    # Dynamic Orientation
    orientation = 'landscape' if room.cols > 7 else 'portrait'
            
    context = {
        'room': room,
        'grid': grid,
        'request': request,
        'orientation': orientation,
    }
    return render_to_pdf('core/pdf_room.html', context)

def download_master_plan_pdf(request):
    """
    Generates a master plan grouped by Semester -> Department -> Room Ranges.
    """
    allocations = SeatAllocation.objects.select_related(
        'student', 'student__semester', 'student__department', 'seat__room'
    ).all()
    
    # Grouping Logic
    from itertools import groupby
    from operator import attrgetter
    
    # Sort for groupby: Semester Num, Dept Code, Roll
    # We sort by objects for grouping, but roll sort needs custom key
    # Helper to get sort key
    def sort_key(alloc):
        sem_num = alloc.student.semester.number
        dept_code = alloc.student.department.code
        # roll handle
        roll = alloc.student.roll_number
        roll_val = int(roll) if roll.isdigit() else roll
        # We can't mix types in tuple easily if roll is mixed. 
        # So convert to string for tuple but use padding for number-like sorting? 
        # Actually, let's sort sequentially.
        return (sem_num, dept_code)
        
    s_allocs = sorted(allocations, key=sort_key)
    
    master_data = [] # [{'semester': name, 'departments': [{'code': code, 'ranges': []}]}]
    
    for semester, sem_iter in groupby(s_allocs, key=attrgetter('student.semester')):
        sem_list = list(sem_iter)
        dept_data = []
        
        for dept, dept_iter in groupby(sem_list, key=attrgetter('student.department')):
            students = list(dept_iter)
            
            # Sort students by roll for range compression
            students.sort(key=lambda x: int(x.student.roll_number) if x.student.roll_number.isdigit() else x.student.roll_number)
            
            # Compress Ranges with Gap Tolerance
            ranges = []
            if students:
                current_range = [students[0]]
                
                for i in range(1, len(students)):
                    prev = current_range[-1]
                    curr = students[i]
                    
                    is_same_room = (prev.seat.room.id == curr.seat.room.id)
                    
                    # Logic: If same room AND numeric difference is small (e.g. < 100), key them together.
                    # This handles "1-10 excluding 9" -> shows "1-10".
                    # And "743610... 756321" -> separate.
                    
                    def get_num(s):
                        import re
                        m = re.findall(r'\d+', s)
                        return int(m[-1]) if m else None

                    p_num = get_num(prev.student.roll_number)
                    c_num = get_num(curr.student.roll_number)
                    
                    is_cluster = False
                    if is_same_room and p_num is not None and c_num is not None:
                        diff = c_num - p_num
                        # Allow gap up to 100 (arbitrary "cluster" size). 
                        # If diff is 1, it's sequential. If 2 (skipped 1), it's "missing".
                        # User wants 1-10 even if 9 missing.
                        if 0 < diff < 100:
                            is_cluster = True
                            
                    if is_cluster:
                        current_range.append(curr)
                    else:
                        ranges.append(_format_range(current_range))
                        current_range = [curr]
                
                if current_range:
                    ranges.append(_format_range(current_range))
            
            dept_data.append({
                'department': dept,
                'ranges': ranges
            })
            
        master_data.append({
            'semester': semester,
            'departments': dept_data
        })
        
    context = {'master_data': master_data}
    return render_to_pdf('core/pdf_master.html', context)

def _format_range(alloc_list):
    first = alloc_list[0]
    last = alloc_list[-1]
    room_name = first.seat.room.name
    
    if len(alloc_list) > 1:
        roll_str = f"{first.student.roll_number} - {last.student.roll_number}"
    else:
        roll_str = first.student.roll_number
        
    return {'rolls': roll_str, 'room': room_name}

@staff_member_required
def download_attendance_pdf(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    allocations = SeatAllocation.objects.filter(seat__room=room).select_related('student', 'student__department', 'student__semester', 'seat').order_by('seat__row', 'seat__col')
    
    if not allocations.exists():
        messages.error(request, "No students allocated to this room.")
        return redirect('dashboard')

    # Sort by Seat Order (Row, Col) as requested: "set plan onujay serial vabe"
    # allocations is already ordered by row, col from the initial query
    
    context = {
        'room': room,
        'allocations': allocations, # Pass raw queryset, sorted by seat
        'generated_at': now()
    }
    
    template_path = 'core/pdf_attendance.html'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attendance_{room.name}_{now().strftime("%Y%m%d")}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

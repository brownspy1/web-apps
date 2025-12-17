import random
from collections import defaultdict
from .models import SeatAllocation

def parse_student_input(input_text):
    """
    Parses input string into a list of roll numbers.
    Supports:
    - Ranges: 1001-1005
    - Individual: 1001, 1002
    - Exclusions: -1003 (removes 1003 from list)
    """
    exclusions = set()
    
    # Normalize newlines to commas
    text = input_text.replace('\n', ',').replace('\r', '')
    
    tokens = [t.strip() for t in text.split(',') if t.strip()]
    
    rolls = set()
    
    for token in tokens:
        is_exclusion = False
        if token.startswith('-'):
            is_exclusion = True
            token = token[1:].strip()
            
        # Parse Range or Single
        current_rolls = []
        if '-' in token:
            try:
                parts = token.split('-')
                if len(parts) == 2:
                    start = int(parts[0])
                    end = int(parts[1])
                    current_rolls = [str(r) for r in range(start, end + 1)]
            except ValueError:
                pass
        else:
            if token.isdigit():
                current_rolls = [token]
                
        for roll in current_rolls:
            if is_exclusion:
                exclusions.add(roll)
            else:
                rolls.add(roll)
                
    # Apply exclusions
    final_rolls = sorted(list(rolls - exclusions), key=lambda x: int(x) if x.isdigit() else x)
    
    # Return list of dicts for compatibility or just list of rolls?
    # Logic in view expects list of dicts with 'roll_number' and 'student_class' (previously).
    # Now view will assign Dept/Sem. So just returning list of rolls is easier, but let's return dicts to keep structure if needed.
    # Actually, let's just return list of strings. View will handle it.
    return final_rolls

def allocate_seats(room, students, algorithm='linear'):
    """
    Allocates students to a room based on the selected algorithm.
    Only considers Seat objects where is_active=True.
    """
    # Get all active seats that are NOT occupied
    # We filter out seats that have an improved 'allocation' relation
    seats = list(room.seats.filter(is_active=True, allocation__isnull=True))
    
    if not seats:
        return []

    # Prepare logic based on algorithm
    # Prepare logic based on algorithm
    if algorithm == 'random':
        random.shuffle(seats)
        
    elif algorithm == 'z_pattern':
        # Vertical Z-Pattern (Snake Column-wise)
        # Col 1: Down, Col 2: Up, Col 3: Down...
        seats_by_col = defaultdict(list)
        for s in seats:
            seats_by_col[s.col].append(s)
            
        z_ordered_seats = []
        cols = sorted(seats_by_col.keys())
        for i, c in enumerate(cols):
            col_seats = sorted(seats_by_col[c], key=lambda s: s.row)
            # Alternate direction: Odd cols (index 0, 2...) = Down (Normal), Even cols (index 1, 3...) = Up (Reverse)?
            # Usually strict Z-pattern: Row 1 L->R... 
            # User wants: "Top to bottom approce" and "Anti cit and Z pattarn... top to bottom"
            # So Column 1 Top->Bottom, then Column 2 Top->Bottom? No, that's N-pattern (Linear Vertical).
            # Z-Pattern usually implies alternating.
            # "Top to bottom approach" for Z-pattern usually means: 
            # Col 1 (1->N), Col 2 (N->1), Col 3 (1->N).
            if i % 2 == 1: # 0-indexed, so 2nd column
                col_seats.reverse()
            z_ordered_seats.extend(col_seats)
        seats = z_ordered_seats
        
    elif algorithm == 'linear_vertical' or algorithm == 'linear': # Treat 'linear' as vertical now if passed by legacy
        # Standard Top-to-Bottom (Column-by-Column)
        seats.sort(key=lambda s: (s.col, s.row))
        
    elif algorithm == 'anti_cheat':
        # Constraint: Student should not have neighbor of Same Department AND Same Semester.
        # Strict logic: If constraints cannot be met, student is NOT allocated.
        
        # Sort seats Top-to-Bottom (Column-major) first
        seats.sort(key=lambda s: (s.col, s.row))
        
        # Heuristic: Interleave by (Department, Semester)
        
        # 1. Group students by (Department, Semester)
        students_by_group = defaultdict(list)
        for s in students:
            key = (s.department_id, s.semester_id)
            students_by_group[key].append(s)
            
        # Interleave
        interleaved_students = []
        while students_by_group:
            keys = list(students_by_group.keys())
            if not keys: break
            
            # Sort keys to ensure deterministic interleaving pattern?
            # Or just random? Deterministic is better for UI predictability.
            keys.sort() 
            
            for k in keys:
                if students_by_group[k]:
                    interleaved_students.append(students_by_group[k].pop(0))
                else:
                    del students_by_group[k]
        
        students = interleaved_students
        return allocate_greedy_anti_cheat(room, seats, students)

    # Standard Allocation Loop
    num_to_allocate = min(len(seats), len(students))
    
    allocations = []
    for i in range(num_to_allocate):
        seat = seats[i]
        student = students[i]
        allocation = SeatAllocation(seat=seat, student=student)
        allocations.append(allocation)
        
    return allocations

def allocate_greedy_anti_cheat(room, seats, students):
    """
    Tries to place students such that no neighbors have the same (Department, Semester).
    Using Strict Mode: Skips students if no valid seat found.
    """
    from .models import SeatAllocation
    
    seat_grid = {}
    for s in seats:
        seat_grid[(s.row, s.col)] = s
        
    neighbors = defaultdict(list)
    for s in seats:
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = s.row + dr, s.col + dc
            if (nr, nc) in seat_grid:
                neighbors[s].append(seat_grid[(nr, nc)])
                
    assigned_seats = {} # {seat: (department_id, semester_id)}
    remaining_seats = list(seats)
    final_allocations = []
    
    for student in students:
        if not remaining_seats:
            break
            
        # Group Key is (Department, Semester)
        s_key = (student.department_id, student.semester_id)
        
        best_seat = None
        best_seat_idx = -1
        
        # Find a valid seat
        for i, seat in enumerate(remaining_seats):
            conflict = False
            for n in neighbors[seat]:
                if n in assigned_seats and assigned_seats[n] == s_key:
                    conflict = True
                    break
            
            if not conflict:
                best_seat = seat
                best_seat_idx = i
                break
        
        # If no valid seat found, SKIP this student (Strict Mode)
        # This prevents constraint violations. 
        # Unallocated students will be caught by the view logic.
        if best_seat is None:
            continue
            
        assigned_seats[best_seat] = s_key
        remaining_seats.pop(best_seat_idx)
        
        allocation = SeatAllocation(seat=best_seat, student=student)
        final_allocations.append(allocation)
        
    return final_allocations

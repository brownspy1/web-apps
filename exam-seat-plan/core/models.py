from django.db import models

class Room(models.Model):
    name = models.CharField(max_length=100)
    rows = models.IntegerField(help_text="Number of rows in the room")
    cols = models.IntegerField(help_text="Number of columns (seats per row)")
    
    @property
    def capacity(self):
        # Return count of active seats
        return self.seats.filter(is_active=True).count()

    def __str__(self):
        return f"{self.name} ({self.rows}x{self.cols})"

class Seat(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='seats')
    row = models.IntegerField()
    col = models.IntegerField()
    is_active = models.BooleanField(default=True, help_text="Is this seat usable?")
    # We can add 'is_walkway' later if needed, but is_active=False is enough for now

    class Meta:
        unique_together = ('room', 'row', 'col')
        ordering = ['row', 'col']

    def __str__(self):
        return f"{self.room.name} - R{self.row}C{self.col}"

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, help_text="Short code e.g. CSE")
    
    def __str__(self):
        return f"{self.code} ({self.name})"

class Semester(models.Model):
    name = models.CharField(max_length=50, help_text="Label e.g. '1st Semester'")
    number = models.IntegerField(unique=True, help_text="Semester Number (1-8)")
    
    def __str__(self):
        return f"{self.name} ({self.number})"

class Student(models.Model):
    roll_number = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='students')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='students')
    
    def __str__(self):
        return f"{self.roll_number} ({self.department.code}-{self.semester.number})"

class SeatAllocation(models.Model):
    seat = models.OneToOneField(Seat, on_delete=models.CASCADE, related_name='allocation', null=True)
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    # Keeping these for quick access, but they are redundant if we have 'seat'
    # Actually, we should link to 'Seat' model now instead of just storing row/col manually
    # But to avoid breaking existing logic instantly, I'll keep them or migrate.
    # Let's switch to using the Seat FK as the source of truth.
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.seat:
            return f"{self.student.roll_number} in {self.seat}"
        return f"{self.student.roll_number} (Unassigned)"

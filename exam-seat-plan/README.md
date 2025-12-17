# Exam Seat Plan Management System

A comprehensive, automated solution for managing exam seat allocations in educational institutions. Designed to handle complex seating constraints, prevent cheating, and provide seamless PDF reporting.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Dashboard+Preview)

## 🚀 Key Featuresweb apps

### 🏛️ Room & Seat Management
- **Dynamic Layouts**: Create rooms of any size (Rows × Columns).
- **Customizable Grids**: Toggle individual seats as "Active" or "Inactive" to account for pillars, walkways, or damaged furniture.
- **Visual Editor**: Interactive grid interface for real-time seat management.

### 🧠 Intelligent Allocation Engine
- **Multiple Algorithms**:
  - **Linear Horizontal**: Standard row-by-row filling.
  - **Linear Vertical**: Column-by-column filling.
  - **Z-Pattern**: Snake-like filling for optimized spacing.
  - **Random**: Complete shuffle for maximum security.
  - **🛡️ Anti-Cheat (Advanced)**: Algorithmically ensures that students of the **same Department AND same Semester** are never seated as neighbors (Front, Back, Left, Right). It intelligently interleaves different departments/semesters and skips students if a valid seat isn't found.
- **Incremental Allocation**: Add students to an already partially filled room without resetting.
- **Handling Overflows**: "Partial Allocation" alerts suggest alternative rooms if the current one reaches capacity or constraint limits.

### 👥 Student Management
- **🤖 AI-Powered OCR**: Upload images of student lists, and the system uses **Google Gemini** to automatically extract Roll Numbers, Departments, and Semesters.
- **Bulk Operations**: 
  - Batch Delete students with "Select All" functionality.
  - Support for manual roll ranges (e.g., `1001-1050`) and exclusions.
- **Metadata Management**: Centralized management for Departments (e.g., CSE, EEE) and Semesters.

### 📄 Professional Reporting (PDF)
- **Room wise Plans**: Printable PDF seat maps for individual rooms.
- **Master Plan**: A consolidated "Notice Board" style PDF listing all students and their assigned rooms.
- **Optimized Layouts**:
  - **Centered Headers**: Perfect alignment for official styling (Barisal Polytechnic Institute).
  - **High Visibility**: Roll numbers and metadata are styled in **Bold Black** for clear printing.
  - **Browser Print Support**: Optimized CSS for direct browser printing (Ctrl+P).

### 🔍 Public & Admin Interfaces
- **Public Search**: Students can search by Roll Number to find their Room, Column, and Row without logging in.
- **Admin Dashboard**: Secure area for staff to manage rooms, students, and allocations.

## 🛠️ Tech Stack
- **Backend**: Django 5.x (Python)
- **Database**: PostgreSQL (Production) / SQLite (Dev)
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism UI), JavaScript
- **AI Integration**: Google Gemini API (for OCR)
- **PDF Engine**: `xhtml2pdf`

## ⚙️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/exam-seat-plan.git
   cd exam-seat-plan
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file for your secrets:
   ```env
   GEMINI_API_KEY=your_key_here
   DB_NAME=your_db
   DB_USER=your_user
   DB_PASSWORD=your_pass
   ```

4. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Start Server**:
   ```bash
   python manage.py runserver
   ```

## 📝 Usage Workflow
1. **Setup**: Add Departments and Semesters in `Manage Metadata`.
2. **Create Room**: Define dimensions (e.g., 5x10). Disable invalid seats by clicking them.
3. **Add Students**: Either manually via `Manage Students` or upload an image in the `Allocation` screen.
4. **Allocate**: Go to a Room -> Click "Allocate Seats" -> Choose Algorithm -> Submit.
5. **Print**: Download PDFs for the Room or the Master Plan.

## 🤝 Contribution
Feel free to open issues or submit pull requests to improve the allocation logic or UI experiences.

---
&copy; 2025 Exam Seat Plan Management System

"""Creates an Excel template for bulk class data entry."""
import json

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "openpyxl"], check=True)
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()

# ===== CLASSES SHEET =====
ws = wb.active
ws.title = "Classes"

# Header styling
header_font = Font(bold=True, color="FFFFFF", size=11)
header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
sub_header_fill = PatternFill(start_color="6366F1", end_color="6366F1", fill_type="solid")
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

# Title
ws.merge_cells('A1:H1')
ws['A1'] = "KKHMS Alathiyur - Class Data Entry Template"
ws['A1'].font = Font(bold=True, size=14, color="4F46E5")

ws.merge_cells('A2:H2')
ws['A2'] = "Fill in the data below. Each row = one class. Upload this file in the app to create classes in bulk."
ws['A2'].font = Font(italic=True, size=10, color="666666")

# Headers (Row 4)
headers = ['Class', 'Divisions', 'Block', 'Type', 'Class Teacher', 'Subject', 'Teacher', 'Periods/Week']
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=4, column=col, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal='center')
    cell.border = thin_border

# Column widths
widths = [8, 15, 15, 25, 20, 20, 20, 14]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

# Subjects list for 8th/9th
subjects_8_9 = [
    'First Language', 'Malayalam II', 'English', 'Hindi', 'Maths',
    'Social Science', 'Chemistry', 'Physics', 'Biology', 'IT',
    'PET', 'Music', 'Work Education', 'Art'
]

# Subjects for 10th
subjects_10 = [
    'First Language', 'Malayalam II', 'English', 'Hindi', 'Maths',
    'Social Science', 'Chemistry', 'Physics', 'Biology', 'IT'
]

# Types
types = [
    'Arabic', 'Malayalam', 'Urdu/Sanskrit', 'Sanskrit/Urdu/Arabic',
    'Malayalam/Arabic', 'Sanskrit/Arabic/Urdu/Malayalam', 'Sanskrit/Arabic',
    'Urdu/Arabic', 'Sanskrit', 'Urdu'
]

# Sample data rows - Class 8 example
row = 5
example_fill = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")

# Write example for Class 8
for i, sub in enumerate(subjects_8_9):
    r = row + i
    if i == 0:
        ws.cell(row=r, column=1, value="8")
        ws.cell(row=r, column=2, value="A, B, C")
        ws.cell(row=r, column=3, value="Block A")
        ws.cell(row=r, column=4, value="Arabic")
        ws.cell(row=r, column=5, value="Teacher Name")
    ws.cell(row=r, column=6, value=sub)
    ws.cell(row=r, column=7, value="")  # Teacher to fill
    ws.cell(row=r, column=8, value=1 if sub in ['PET', 'Music', 'Work Education', 'Art'] else "")
    for c in range(1, 9):
        ws.cell(row=r, column=c).border = thin_border
        ws.cell(row=r, column=c).fill = example_fill

# Add empty rows for Class 9
row = row + len(subjects_8_9) + 1
ws.cell(row=row, column=1, value="9").font = Font(bold=True)
for i, sub in enumerate(subjects_8_9):
    r = row + i
    if i == 0:
        ws.cell(row=r, column=1, value="9")
        ws.cell(row=r, column=2, value="A, B, C")
        ws.cell(row=r, column=3, value="Block A")
        ws.cell(row=r, column=4, value="")
        ws.cell(row=r, column=5, value="")
    ws.cell(row=r, column=6, value=sub)
    ws.cell(row=r, column=7, value="")
    ws.cell(row=r, column=8, value=1 if sub in ['PET', 'Music', 'Work Education', 'Art'] else "")
    for c in range(1, 9):
        ws.cell(row=r, column=c).border = thin_border

# Add empty rows for Class 10
row = row + len(subjects_8_9) + 1
for i, sub in enumerate(subjects_10):
    r = row + i
    if i == 0:
        ws.cell(row=r, column=1, value="10")
        ws.cell(row=r, column=2, value="A, B")
        ws.cell(row=r, column=3, value="Block B")
        ws.cell(row=r, column=4, value="")
        ws.cell(row=r, column=5, value="")
    ws.cell(row=r, column=6, value=sub)
    ws.cell(row=r, column=7, value="")
    ws.cell(row=r, column=8, value="")
    for c in range(1, 9):
        ws.cell(row=r, column=c).border = thin_border

# ===== INSTRUCTIONS SHEET =====
ws2 = wb.create_sheet("Instructions")
instructions = [
    "HOW TO FILL THIS TEMPLATE",
    "",
    "1. Each CLASS starts on the row where Column A (Class) has a value (8, 9, or 10)",
    "2. Column B (Divisions): Enter division letters separated by commas (e.g., A, B, C)",
    "3. Column C (Block): Enter the block name exactly as created in the app",
    "4. Column D (Type): Arabic, Malayalam, Urdu/Sanskrit, Sanskrit/Urdu/Arabic, etc.",
    "5. Column E (Class Teacher): Enter teacher name exactly as in the app",
    "6. Column F (Subject): Pre-filled. Do not change.",
    "7. Column G (Teacher): Enter the teacher name who teaches this subject for this class",
    "8. Column H (Periods/Week): Enter number of periods per week for each subject",
    "",
    "RULES:",
    "- Total periods per class MUST equal 35 (5 days × 7 periods)",
    "- PET, Music, Work Education, Art are fixed at 1 period/week (Class 8 & 9 only)",
    "- Class 10 does NOT have PET, Music, WE, Art",
    "- Teacher names must match exactly with the names in the Teachers list",
    "",
    "TYPES AVAILABLE:",
    "  Arabic, Malayalam, Urdu/Sanskrit, Sanskrit/Urdu/Arabic,",
    "  Malayalam/Arabic, Sanskrit/Arabic/Urdu/Malayalam, Sanskrit/Arabic,",
    "  Urdu/Arabic, Sanskrit, Urdu",
    "",
    "After filling, upload this file in the app using the 'Upload Excel' button on the Classes page."
]

for i, line in enumerate(instructions, 1):
    ws2.cell(row=i, column=1, value=line)
    if i == 1:
        ws2.cell(row=i, column=1).font = Font(bold=True, size=14)
    elif line.startswith("RULES:") or line.startswith("TYPES"):
        ws2.cell(row=i, column=1).font = Font(bold=True)

ws2.column_dimensions['A'].width = 80

# Save
output_path = r"c:\Users\mushkott\Desktop\Python Projects\school-timetable\class_template.xlsx"
wb.save(output_path)
print(f"✅ Template created: {output_path}")

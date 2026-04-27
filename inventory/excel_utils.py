import openpyxl
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
import os
from django.conf import settings

# Column order: Type(0), Item Name(1), Size(2), Length(3), Quantity(4), Location(5), Description(6), Image Path(7)
COLUMNS = ['Type', 'Item Name', 'Size', 'Length', 'Quantity', 'Location', 'Description', 'Image Path','User']

# Column index constants (0-based for row[], 1-based for openpyxl col refs)
COL_TYPE        = 0
COL_ITEM_NAME   = 1
COL_SIZE        = 2
COL_LENGTH      = 3
COL_QUANTITY    = 4
COL_LOCATION    = 5
COL_DESCRIPTION = 6
COL_IMAGE_PATH  = 7
COL_USER = 8


def get_or_create_workbook():
    path = settings.EXCEL_FILE_PATH

    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        wb = load_workbook(path)
    else:
        wb = openpyxl.Workbook()

    # Remove default empty sheets
    if "Sheet" in wb.sheetnames:
        wb.remove(wb["Sheet"])

    if "Inventory" in wb.sheetnames:
        wb.remove(wb["Inventory"])

    return wb


def _style_header(ws):
    header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True, size=12)

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Column widths matching: Type, Item Name, Size, Length, Quantity, Location, Description, Image Path
    ws.column_dimensions['A'].width = 15  # Type
    ws.column_dimensions['B'].width = 20  # Item Name
    ws.column_dimensions['C'].width = 10  # Size
    ws.column_dimensions['D'].width = 10  # Length
    ws.column_dimensions['E'].width = 12  # Quantity
    ws.column_dimensions['F'].width = 20  # Location
    ws.column_dimensions['G'].width = 30  # Description
    ws.column_dimensions['H'].width = 40  # Image Path


def append_inventory_item(item_type, item_name, size, length, quantity, location, description, department, image_path):
    wb = get_or_create_workbook()

    if not department:
        raise ValueError("Department is required")

    sheet_name = department.strip()
    image_path = image_path if image_path else ''

    # Create sheet with header if it doesn't exist yet
    if sheet_name not in wb.sheetnames:
        ws = wb.create_sheet(title=sheet_name)
        ws.append(COLUMNS)
        _style_header(ws)
    else:
        ws = wb[sheet_name]

    # Append row in correct column order
    ws.append([
        item_type,    # A - Type
        item_name,    # B - Item Name
        size,         # C - Size
        length,       # D - Length
        quantity,     # E - Quantity
        location,     # F - Location
        description,  # G - Description
        image_path,
        ''   # H -  # empty user initially
    ])

    wb.save(settings.EXCEL_FILE_PATH)


def read_inventory_items():
    path = settings.EXCEL_FILE_PATH

    if not os.path.exists(path):
        return []

    wb = load_workbook(path)
    items = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]

        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue  # skip header
            if not row or row[COL_TYPE] is None:
                continue

            items.append({
                'item_type':   str(row[COL_TYPE])        if len(row) > COL_TYPE        else '',
                'item_name':   str(row[COL_ITEM_NAME])   if len(row) > COL_ITEM_NAME   else '',
                'size':        str(row[COL_SIZE])         if len(row) > COL_SIZE         else '',
                'length':      str(row[COL_LENGTH])       if len(row) > COL_LENGTH       else '',
                'quantity':    int(row[COL_QUANTITY])     if len(row) > COL_QUANTITY and str(row[COL_QUANTITY]).isdigit() else 0,
                'location':    str(row[COL_LOCATION])     if len(row) > COL_LOCATION     else '',
                'description': str(row[COL_DESCRIPTION])  if len(row) > COL_DESCRIPTION  else '',
                'image_path':  str(row[COL_IMAGE_PATH])   if len(row) > COL_IMAGE_PATH and row[COL_IMAGE_PATH]   else '',
            })

    return items


def reduce_inventory_quantity(item_name, quantity_to_reduce, department):
    path = settings.EXCEL_FILE_PATH

    if not os.path.exists(path):
        return

    wb = load_workbook(path)

    if department not in wb.sheetnames:
        return

    ws = wb[department]

    for row in ws.iter_rows(min_row=2):
        # ✅ FIXED: Item Name is now column index 1 (B), not 0 (A)
        if row[COL_ITEM_NAME].value == item_name:
            current_qty = row[COL_QUANTITY].value or 0
            new_qty = max(0, current_qty - quantity_to_reduce)
            row[COL_QUANTITY].value = new_qty
            break

    wb.save(path)

def update_inventory_item(item_name, old_size, old_length, department, **kwargs):
    path = settings.EXCEL_FILE_PATH
    if not os.path.exists(path):
        return

    wb = load_workbook(path)
    if department not in wb.sheetnames:
        return

    ws = wb[department]

    old_type = None
    new_type = kwargs.get('item_type')
    def normalize_length(val):
        try:
            return str(float(val))
        except:
            return str(val).strip().lower()

    # Step 1: Find the row and store old type
    for row in ws.iter_rows(min_row=2):
        if (
            str(row[COL_ITEM_NAME].value).strip().lower() == str(item_name).strip().lower() and
            str(row[COL_SIZE].value).strip().lower() == str(old_size).strip().lower() and
            normalize_length(row[COL_LENGTH].value) == normalize_length(old_length)
        ):
            old_type = row[COL_TYPE].value

            if 'new_item_name' in kwargs:
                row[COL_ITEM_NAME].value = kwargs['new_item_name']

            if 'item_type' in kwargs:
                row[COL_TYPE].value = kwargs['item_type']

            if 'size' in kwargs:
                row[COL_SIZE].value = kwargs['size']

            if 'length' in kwargs:
                row[COL_LENGTH].value = kwargs['length']

            if 'quantity' in kwargs:
                row[COL_QUANTITY].value = kwargs['quantity']

            if 'location' in kwargs:
                row[COL_LOCATION].value = kwargs['location']
            if 'user' in kwargs:
                row[COL_USER].value = kwargs['user']

            break

    #  Step 2: Update ALL rows with same old type
    if old_type and new_type:
        for row in ws.iter_rows(min_row=2):
            current_type = str(row[COL_TYPE].value).strip()

            if current_type.lower() == str(old_type).strip().lower():
                row[COL_TYPE].value = new_type

    wb.save(path)

def delete_inventory_item(item_name, department):
    path = settings.EXCEL_FILE_PATH
    if not os.path.exists(path):
        return
    wb = load_workbook(path)
    if department not in wb.sheetnames:
        return
    ws = wb[department]
    for row in ws.iter_rows(min_row=2):
        if row[COL_ITEM_NAME].value == item_name:
            ws.delete_rows(row[0].row)
            break
    wb.save(path)


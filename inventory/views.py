# from django.http import FileResponse, HttpResponse
# from django.conf import settings
# import os

# def download_excel(request):
#     file_path = settings.EXCEL_FILE_PATH

#     if not os.path.exists(file_path):
#         return HttpResponse("File not found", status=404)

#     return FileResponse(
#         open(file_path, 'rb'),
#         as_attachment=True,
#         filename="inventory.xlsx"
#     )

import openpyxl
from django.http import HttpResponse
from .models import InventoryItem

def download_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventory"
    
    # Header
    ws.append(['Type', 'Item Name', 'Size', 'Length', 'Quantity', 'Location', 'Description', 'Department'])

    # Read from DB
    for item in InventoryItem.objects.all():
        ws.append([
            item.item_type,
            item.item_name,
            item.size,
            item.length,
            item.quantity,
            item.location,
            item.description,
            item.department,
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=inventory.xlsx'
    wb.save(response)
    return response
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
from .models import InventoryItem, IssuedItem

def download_excel(request):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # remove default empty sheet

    # Get all unique departments
    departments = InventoryItem.objects.values_list('department', flat=True).distinct()

    for department in departments:
        ws = wb.create_sheet(title=department or 'Unknown')
        
        # Header
        ws.append(['Type', 'Item Name', 'Size', 'Length', 'Quantity', 'Location', 'Description', 'User'])

        # Filter items by department
        items = InventoryItem.objects.filter(department__iexact=department)
        
        for item in items:
            issued = IssuedItem.objects.filter(
                item_name__iexact=item.item_name
            ).order_by('-issued_at').first()

            user_name = ''
            if issued and issued.issued_to:
                user_name = issued.issued_to.name

            ws.append([
                item.item_type,
                item.item_name,
                item.size,
                item.length,
                item.quantity,
                item.location,
                item.description,
                user_name,
            ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=inventory.xlsx'
    wb.save(response)
    return response
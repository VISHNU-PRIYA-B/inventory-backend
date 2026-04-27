from django.http import FileResponse, HttpResponse
from django.conf import settings
import os

def download_excel(request):
    file_path = settings.EXCEL_FILE_PATH

    if not os.path.exists(file_path):
        return HttpResponse("File not found", status=404)

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename="inventory.xlsx"
    )
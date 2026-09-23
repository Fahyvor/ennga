from django.contrib import admin
from .models import (
    SearchData, 
    SearchDataImport, 
    SearchDataBookmark,
    SearchDataExport,
    SearchDataShare,
    SearchDataUpload,
)

admin.site.register(SearchData)
admin.site.register(SearchDataImport)
admin.site.register(SearchDataBookmark)
admin.site.register(SearchDataExport)
admin.site.register(SearchDataShare)
admin.site.register(SearchDataUpload)
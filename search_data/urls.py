from django.urls import path
from .views import (
    SearchDocumentView,
    SearchDataTotalListAPIView,
    SearchDataImportListAPIView,
    SearchDataImportAPIView,
    SearchDataExportListAPIView,
    SearchDataExportAPIView,
    SearchDataBookmarkListAPIView,
    SearchDataBookmarkAPIView,
    SearchDataBookmarkDeleteAPIView,
    SearchDataCreateAPIView,
    SearchDataUpdateAPIView,
    SearchDataDeleteAPIView,
    SearchDataShareAPIView,
    SearchDataRetrieveAPIView,
    
    SearchDataUploadCreateView,
    SearchDataUploadDetailView,
    SearchDataUploadUpdateView,
    SearchDataUploadListView,
    SearchDataUploadDeleteView,
    SearchDataCountAPIView,
    SearchDataTopSearchesView,
    SearchDataDownloadsCreateAPIView
    )


app_name = "search_data"
urlpatterns = [
    path("search/", SearchDocumentView.as_view({'get': 'list'})),
    path("search/create/", SearchDataCreateAPIView.as_view()),
    path("search/update/<int:pk>/", SearchDataUpdateAPIView.as_view()),
    path("search/delete/<int:pk>/", SearchDataDeleteAPIView.as_view()),
    path("search/retrieve/<int:pk>/", SearchDataRetrieveAPIView.as_view()),
    
    path("search/share/", SearchDataShareAPIView.as_view()),
    path("search/total/<int:pk>/", SearchDataTotalListAPIView.as_view()),
    path("search/import/list/",SearchDataImportListAPIView.as_view() ),
    path("search/import/",SearchDataImportAPIView.as_view()),
    
    path("search/export/list/",SearchDataExportListAPIView.as_view() ),
    path("search/export/",SearchDataExportAPIView.as_view()),


    path("search/bookmark/list/",SearchDataBookmarkListAPIView.as_view()),
    path("search/bookmark/",SearchDataBookmarkAPIView.as_view()),
    path("search/bookmark/delete/",SearchDataBookmarkDeleteAPIView.as_view()),
    
    path("search/upload/create/",SearchDataUploadCreateView.as_view()),
    path("search/upload/update/<int:pk>/", SearchDataUploadUpdateView.as_view()),
    path("search/upload/list/",SearchDataUploadListView.as_view()),
    path("search/upload/delete/<int:pk>/",SearchDataUploadDeleteView.as_view()),
    path("search/upload/retrieve/<int:pk>/",SearchDataUploadDetailView.as_view()),
    path("search/top/",SearchDataTopSearchesView.as_view()),
    path("search/count/", SearchDataCountAPIView.as_view()),
    path("search/downloads/", SearchDataDownloadsCreateAPIView.as_view()),
    
]
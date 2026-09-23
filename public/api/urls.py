from django.urls import path
from .views import (ContactUsAPIView,
                    FAQListAPIView, 
                    FAQDetailAPIView)

app_name = 'public_api'
urlpatterns = [
    path("contact-us/",ContactUsAPIView.as_view(), name="contact-us"),
    path("faq/",FAQListAPIView.as_view(), name="faq"),
    path("faq/<int:pk>/",FAQDetailAPIView.as_view(), name="faq-details")
]



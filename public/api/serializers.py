from rest_framework import serializers
from ..models import ContactUs, FAQ

class ContactUsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactUs
        fields = [
            "email", 
            "full_name", 
            "contact_message"
            ]


class FAQListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["id", "title", "faq_message"]

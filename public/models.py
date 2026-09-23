from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField

class ContactUs(models.Model):
    user = models.ForeignKey("accounts.Profile", blank=True, null=True, on_delete=models.SET_NULL)
    email = models.EmailField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    contact_message = RichTextUploadingField()
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class FAQ(models.Model):
    title = models.CharField(max_length=255)
    faq_message = RichTextUploadingField()
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)
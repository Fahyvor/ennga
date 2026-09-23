from django.core.exceptions import ValidationError

def validate_file_extension(value):
    valid_extensions = ['json', 'pdf', 'csv', 'ppt', 'pptx']
    extension = value.name.split('.')[-1].lower()
    if extension not in valid_extensions:
        raise ValidationError(f"Unsupported file extension. Allowed extensions are: {', '.join(valid_extensions)}")
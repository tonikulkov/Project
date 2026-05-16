from django import forms
from .models import Document
from django.core.exceptions import ValidationError
import magic
import os

MAX_FILE_SIZE = 40 * 1024 * 1024 
def validate_file_size(value):
    if value.size > MAX_FILE_SIZE:
        raise ValidationError(f'Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE / (1024 * 1024)} МБ.')
    
def validate_file_mime_type(value):
    ext = os.path.splitext(value.name)[1].lower()
    file_header = value.read(1024)
    value.seek(0)
    mime_type = magic.from_buffer(file_header, mime=True)
    allowed_mimes = [
        'application/pdf',                                      
        'application/msword',                                   
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
        'application/vnd.ms-excel',                             
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',       
        'application/vnd.ms-powerpoint',                        
        'application/vnd.openxmlformats-officedocument.presentationml.presentation' 
    ]
    if mime_type == 'application/octet-stream':
        safe_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
        if ext in safe_extensions:
            return
    if mime_type in allowed_mimes:
        return
    raise ValidationError(
        f'Недопустимый формат файла (система определила: {mime_type}). '
        'Разрешены только документы PDF, Word, Excel, Powerpoint.'
    )
    
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({
            'class': 'form-file-input',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx'
        })
        self.fields['file'].validators.append(validate_file_mime_type)
        self.fields['file'].validators.append(validate_file_size)
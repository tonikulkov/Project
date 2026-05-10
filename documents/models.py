import hashlib
import os

from django.db import models
from django.contrib.auth.models import User

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")
    level = models.IntegerField(default=0, verbose_name="Уровень доступа") 

    
    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.username} - {self.role}"
class Document(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название документа")
    file = models.FileField(upload_to='documents/%Y/%m/%d/', verbose_name="Файл")
    file_extension = models.CharField(max_length=10, blank=True, verbose_name="Расширение файла")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Загрузил")
    access_level = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Уровень доступа")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    file_hash = models.CharField(max_length=64, unique=True, blank=True, null=True, verbose_name="Хеш SHA-256")

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file:
            ext = os.path.splitext(self.file.name)[1] 
            self.file_extension = ext.lower() 

            self.file_hash = self._calculate_hash()
            
        super().save(*args, **kwargs)

    def _calculate_hash(self):
        sha256_hash = hashlib.sha256()
        self.file.open(mode='rb') 
        for chunk in self.file.chunks():
            sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
class ViewHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='view_history')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='viewers')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'document')
        verbose_name_plural = "История просмотра"
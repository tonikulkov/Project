from django.contrib import admin
from .models import Document, Role, UserProfile, ViewHistory

# Register your models here.
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'level')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_extension', 'uploaded_by', 'access_level', 'uploaded_at')
    list_filter = ('uploaded_at', 'file_extension', 'access_level', 'uploaded_by')
    search_fields = ('title','uploaded_by__username')
    readonly_fields = ('file_hash', 'uploaded_at')
@admin.register(ViewHistory)
class ViewHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'document', 'viewed_at')
    list_filter = ('viewed_at', 'user')
    search_fields = ('user__username', 'document__title')
    readonly_fields = ('viewed_at',)
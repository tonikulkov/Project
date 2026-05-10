from django.urls import path
from . import views
from django.contrib.auth.views import LoginView


urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('auth/', views.user_login, name='user_login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('upload/', views.upload_document, name='upload_document'),
    path('delete/<int:doc_id>/', views.delete_document, name='delete_document'),
    path('view/<int:doc_id>/', views.view_document, name='view_document'),
    path('documents/callback/<int:doc_id>/', views.document_callback, name='document_callback'),
    path('all_documents/', views.all_documents, name='all_documents'),
    path('edit/<int:doc_id>/', views.edit_document, name='edit_document'),
    path('my-documents/', views.my_documents, name='my_documents'),
]
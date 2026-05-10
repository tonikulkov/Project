from django.utils import timezone
import json
from django.db import IntegrityError
from django.http import JsonResponse
import requests
from django.shortcuts import  get_object_or_404, render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from documents.models import Document, Role, ViewHistory
from django.conf import settings
from .forms import DocumentUploadForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import os
def get_docs_with_icons(documents):
    docs_list = []
    for doc in documents:
        ext = doc.file_extension.lower()
        if ext in ['.pdf']:
            icon_name = 'pdf-256.png'
        elif ext in ['.doc', '.docx']:
            icon_name = 'doc ico.png' 
        elif ext in ['.xls', '.xlsx']:
            icon_name = 'TableIco.png'
        elif ext in ['.ppt', '.pptx']:
            icon_name = 'powerpoint-256.png'
        else:
            icon_name = 'doc ico.png' 
        
        docs_list.append({
            'doc': doc, 
            'icon': icon_name
        })
    return docs_list
@never_cache
@login_required
def document_list(request):
    last_download_docs = Document.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')[:4]
    viewed_docs_ids = list(ViewHistory.objects.filter(user=request.user).values_list('document_id', flat=True).order_by('-viewed_at')[:5])
    last_viewed_docs = list(Document.objects.filter(id__in=viewed_docs_ids))
    last_viewed_docs.sort(key=lambda doc: viewed_docs_ids.index(doc.id))

    context = {
        'uploaded_documents': get_docs_with_icons(last_download_docs),
        'viewed_documents': get_docs_with_icons(last_viewed_docs),
    }
    return render(request, 'documents/index.html', context)

@never_cache
def user_login(request):
    if request.user.is_authenticated:
        return redirect('document_list')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('document_list')
        else:
            messages.error(request, "Неверный логин или пароль.")
        
    else:
        form = AuthenticationForm()
    
    return render(request, 'documents/login.html', {'form': form})

@never_cache
def register(request):
    if request.user.is_authenticated:
        return redirect('document_list')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно! Добро пожаловать.")
            return redirect('document_list')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    field_obj = form.fields.get(field)
                    label = field_obj.label if field_obj else "Ошибка"
                    error_messages.append(f"{label}: {error}")
            full_error_text = "<br>".join(error_messages)
            messages.error(request, full_error_text, extra_tags='safe')
    else:
        form = UserCreationForm()
    return render(request, 'documents/register.html', {'form': form})

@never_cache
def user_logout(request):
    logout(request)
    return redirect('user_login')

@never_cache
@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            original_filename = request.FILES['file'].name
            doc.title = os.path.splitext(original_filename)[0]
            if hasattr(request.user, 'profile') and request.user.profile.role:
                doc.access_level = request.user.profile.role 
            doc.uploaded_by = request.user
            try:
                doc.save()
                messages.success(request, f"Файл '{doc.title}' успешно загружен!")
                form = DocumentUploadForm() 
            except IntegrityError:
                messages.error(request, "Такой файл уже хранится в системе.")
    else:
        form = DocumentUploadForm()
    return render(request, 'upload.html', {'form': form})

@never_cache
@login_required
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id) 
    user_role_name = None
    if hasattr(request.user, 'profile') and request.user.profile.role:
        user_role_name = request.user.profile.role.name
    if request.user == doc.uploaded_by or request.user.is_superuser or user_role_name == "Начальник":
        try:
            if doc.file:
                if os.path.isfile(doc.file.path):
                    os.remove(doc.file.path)
            doc.delete()
            messages.success(request, "Документ успешно удален.")
        except Exception as e:
            messages.error(request, f"Ошибка при удалении: {e}")
    else:
        messages.error(request, "У вас нет прав для удаления этого документа.")
    next_url =request.GET.get('next')
    if next_url:
        return redirect(next_url)
    else:
        return redirect('document_list')

@never_cache 
@login_required
def view_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    ViewHistory.objects.update_or_create(
        user=request.user,
        document=doc,
        defaults={'viewed_at': timezone.now()}
    )
    BASE_HOST = "http://nginx"
    file_url = f"{BASE_HOST}{doc.file.url}"
    callback_url = f"{BASE_HOST}/documents/callback/{doc.id}/"
    api_url_js = "http://127.0.0.1:8080/web-apps/apps/api/documents/api.js"
    context = {
        'document': doc,
        'api_url': api_url_js,
        'file_url': file_url,
        'callback_url': callback_url,
    }
    return render(request, 'documents/view.html', context)
@csrf_exempt
def document_callback(request, doc_id):
    if request.method != 'POST':
        return JsonResponse({"error": 1})
    try:
        body = json.loads(request.body)
        status = body.get('status')
        if status in [2, 6]:
            doc = get_object_or_404(Document, id=doc_id)
            download_uri = body.get('url')
            if download_uri:
                if "127.0.0.1:8080" in download_uri or "localhost:8080" in download_uri:
                    download_uri = download_uri.replace("http://127.0.0.1:8080", "http://host.docker.internal:8080")
                    download_uri = download_uri.replace("http://localhost:8080", "http://host.docker.internal:8080")
                response = requests.get(download_uri, timeout=15, verify=False)
                
                if response.status_code == 200:
                    with open(doc.file.path, 'wb') as f:
                        f.write(response.content)

                    doc.file_hash = doc._calculate_hash()
                    doc.save(update_fields=['file_hash'])

        return JsonResponse({"error": 0})
    except Exception:
        return JsonResponse({"error": 1})
    
@login_required
def all_documents(request):
    user_role = request.user.profile.role
    if user_role:
        docs = Document.objects.filter(access_level__level__lte=user_role.level).order_by('-uploaded_at')
    else:
        docs = Document.objects.none()
    max_lvl = request.GET.get('max_level')
    if max_lvl:
        docs = docs.filter(access_level__level__lte=max_lvl)
    roles = Role.objects.filter(level__lte=user_role.level).order_by('level')
    return render(request, 'documents/all_documents.html', {'documents':  get_docs_with_icons(docs), 'user_role': user_role, 'roles': roles, 'selected_lvl': max_lvl})
@never_cache 
@login_required
def edit_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    ViewHistory.objects.update_or_create(
        user=request.user,
        document=doc,
        defaults={'viewed_at': timezone.now()}
    )
    BASE_HOST = "http://nginx"
    file_url = f"{BASE_HOST}{doc.file.url}"
    callback_url = f"{BASE_HOST}/documents/callback/{doc.id}/"
    api_url_js = "http://127.0.0.1:8080/web-apps/apps/api/documents/api.js"
    context = {
        'document': doc,
        'api_url': api_url_js,
        'file_url': file_url,
        'callback_url': callback_url,
    }
    return render(request, 'documents/edit.html', context)

@never_cache
@login_required
def my_documents(request):
    documents = Document.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    return render(request, 'documents/my_documents.html', {'documents':  get_docs_with_icons(documents)})
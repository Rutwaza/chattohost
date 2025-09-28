"""from django.contrib import admin
from .models import CustomUser, ChatGroup, Message

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'phone']

@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'admin', 'created_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'group', 'content', 'created_at']"""

# chat/admin.py
from django.contrib import admin
from django.apps import apps

# Auto-register every model in this app
app = apps.get_app_config('chat')
for model_name, model in app.models.items():
    class GenericAdmin(admin.ModelAdmin):
        list_display = [field.name for field in model._meta.fields]
        list_filter  = [field.name for field in model._meta.fields if field.get_internal_type() not in ("TextField",)]
        search_fields = [field.name for field in model._meta.fields if field.get_internal_type() in ("CharField", "TextField")]
    admin.site.register(model, GenericAdmin)

# chat/urls.py
from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.landing_page, name="landing"), 
    path("register/", views.register, name="register"),
    path("login/", views.secret_login, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("room/", views.chat_room, name="chat_room"),
    path('clear/', views.clear_chat, name='clear_chat'),
]

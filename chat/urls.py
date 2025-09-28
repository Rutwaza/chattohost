# chat/urls.py
from django.urls import path
from . import views
from django.contrib import admin


app_name = "chat"

urlpatterns = [

    path('', views.landing_page, name='landing'),
    path("register/", views.register, name="register"),
    path("login/", views.secret_login, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("founder/", views.founder, name="founder"),
    path("delete_user/<int:user_id>/", views.delete_user, name="delete_user"),

    path('index/', views.index, name='index'),
    path('create/', views.create_group, name='create_group'),
    path('join/', views.join_group, name='join_group'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),
    path('message/delete/<int:message_id>/', views.delete_message, name='delete_message'),

    path('group/<int:group_id>/delete/', views.delete_group, name='delete_group'),
    path('group/<int:group_id>/members/', views.group_members, name='group_members'),
    path('group/<int:group_id>/remove/<int:user_id>/', views.remove_member, name='remove_member'),
    path('message/<int:message_id>/pin/', views.toggle_pin, name='toggle_pin')
]
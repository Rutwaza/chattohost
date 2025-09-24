# chat/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm, SecretLoginForm
from .models import CustomUser
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from .models import Message
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect("chat:login")
    else:
        form = CustomUserCreationForm()
    return render(request, "chat/register.html", {"form": form})

def secret_login(request):
    if request.method == "POST":
        form = SecretLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("chat:chat_room")
    else:
        form = SecretLoginForm()
    return render(request, "chat/login.html", {"form": form})

def landing_page(request):
    return render(request, 'chat/landing.html')

def founder(request):
    return render(request, 'chat/founder.html')

def logout_view(request):
    logout(request)
    return redirect("chat:login")  # redirect to your login page

def chat_room(request):
    if not request.user.is_authenticated:
        return redirect("chat:login")
    messages = Message.objects.order_by('-timestamp')[:50]  # newest first
    messages = reversed(messages)  # so newest appear at the bottom
    return render(request, 'chat/room.html', {'messages': messages})

@login_required
def clear_chat(request):
    if request.user.is_superuser:  # only allow admin to clear
        Message.objects.all().delete()
    return redirect('chat:chat_room')  # or the URL name for your chat room
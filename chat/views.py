# chat/views.py
from django.contrib.auth import login
from .forms import CustomUserCreationForm, SecretLoginForm
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CustomUser, ChatGroup, Message
from django.contrib import messages

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
            return redirect("chat:index")  # redirect to your desired page after login
    else:
        form = SecretLoginForm()
    return render(request, "chat/login.html", {"form": form})

def landing_page(request):
    return render(request, 'chat/landing.html')

def founder(request):
    return render(request, 'chat/founder.html')

def logout_view(request):
    logout(request)
    return redirect("chat:landing")

@staff_member_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('admin_dashboard')

################################################################################

# Landing / Index page
@login_required
def index(request):
    """Show all groups user can join or create new group."""
    query = request.GET.get('q', '')
    groups = ChatGroup.objects.filter(name__icontains=query)
    return render(request, 'chat/index.html', {'groups': groups, 'query': query})

# Create a group
@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        secret_key = request.POST.get('secret_key')
        if ChatGroup.objects.filter(secret_key=secret_key).exists():
            messages.error(request, 'Secret key already exists.')
        else:
            group = ChatGroup.objects.create(name=name, secret_key=secret_key, admin=request.user)
            group.members.add(request.user)
            messages.success(request, f'Group "{name}" created!')
            return redirect('chat:group_detail', group_id=group.id)
    return render(request, 'chat/create_group.html')

# Join a group
@login_required
def join_group(request):
    if request.method == 'POST':
        secret_key = request.POST.get('secret_key')
        try:
            group = ChatGroup.objects.get(secret_key=secret_key)
            group.members.add(request.user)
            messages.success(request, f'You joined "{group.name}"!')
            return redirect('chat:group_detail', group_id=group.id)
        except ChatGroup.DoesNotExist:
            messages.error(request, 'Invalid secret key.')
    return render(request, 'chat/join_group.html')

# Group chat page
@login_required
def group_detail(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)
    if request.user not in group.members.all():
        messages.error(request, 'You are not a member of this group.')
        return redirect('chat:index')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(group=group, user=request.user, content=content)
    
    #messages_list = group.messages.order_by('created_at')
    messages_list= group.messages.order_by('-pinned', 'created_at')

    return render(request, 'chat/group_detail.html', {'group': group, 'messages': messages_list})

# Delete message (admin only)
@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user != message.group.admin:
        messages.error(request, 'Only the admin can delete messages.')
    else:
        message.delete()
        messages.success(request, 'Message deleted.')
    return redirect('chat:group_detail', group_id=message.group.id)

# Remove member (admin only)
@login_required
def remove_member(request, group_id, user_id):
    group = get_object_or_404(ChatGroup, id=group_id)
    if request.user != group.admin:
        messages.error(request, 'Only the admin can remove members.')
    else:
        user = get_object_or_404(CustomUser, id=user_id)
        group.members.remove(user)
        messages.success(request, f'{user.username} removed from the group.')
    return redirect('chat:group_detail', group_id=group.id)


@login_required
def group_members(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)
    members = group.members.all()
    return render(request, 'chat/group_members.html', {
        'group': group,
        'members': members
    })

@login_required
def remove_member(request, group_id, user_id):
    group = get_object_or_404(ChatGroup, id=group_id)
    if request.user != group.admin:
        messages.error(request, "Only the group creator can remove members.")
        return redirect('chat:group_members', group_id=group.id)

    member = get_object_or_404(CustomUser, id=user_id)
    if member == group.admin:
        messages.warning(request, "You cannot remove the creator.")
    else:
        group.members.remove(member)
        messages.success(request, f"{member.username} removed from the group.")
    return redirect('chat:group_members', group_id=group.id)

@login_required
def delete_group(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)
    if request.user != group.admin:
        messages.error(request, "Only the creator can delete this group.")
        return redirect('chat:group_detail', group_id=group.id)

    group.delete()
    messages.success(request, "Group deleted successfully.")
    return redirect('chat:index')

@login_required
def toggle_pin(request, message_id):
    """
    Toggle pinned/unpinned state of a message.
    Only the group admin can pin/unpin.
    """
    message = get_object_or_404(Message, id=message_id)
    group = message.group

    # Check admin privilege
    if request.user == group.admin:
        message.pinned = not message.pinned
        message.save()

    # Always redirect back to the group detail page
    return redirect('chat:group_detail', group_id=group.id)
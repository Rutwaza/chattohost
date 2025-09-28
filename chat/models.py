# chat/models.py
from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.conf import settings

# Custom user model
class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)
    secret_code = models.CharField(max_length=50, blank=True, null=True)

    # Remove default groups conflict by renaming field
    chat_groups = models.ManyToManyField(
        'ChatGroup',
        related_name='members',   # groups can still access their users via group.members
        blank=True
    )

    # User permissions
    user_permissions_custom = models.ManyToManyField(
        Permission,
        related_name='customuser_set_custom',
        blank=True,
        help_text='Specific permissions for this user.'
    )

    def __str__(self):
        return self.username

class ChatGroup(models.Model):
    name = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=20, unique=True)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (admin: {self.admin.username})"

class Message(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    seen_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='seen_messages', blank=True)
    pinned = models.BooleanField(default=False)   # ✅ NEW
    audio = models.FileField(upload_to="messages/audio/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def to_dict(self):
        """Convenience method for serializing to client payloads."""
        return {
            "id": self.id,
            "user": self.user.username,
            "user_id": self.user.id,
            "content": self.content,
            "image_url": self.image.url if self.image else None,
            "reply_to": self.reply_to.id if self.reply_to else None,
            "reply_text": self.reply_to.content if self.reply_to else None,
            "seen_count": self.seen_by.count(),
            "timestamp": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "audio": self.audio.url if self.audio else None,   
        }

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"

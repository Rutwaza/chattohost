import json
import base64
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile

# Shared set to track online users
active_users = set()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "chat_main"
        user = self.scope["user"]
        if user.is_authenticated:
            active_users.add(user.username)  # ✅ add user to active set

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Broadcast updated online count
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "online_count",
                "count": len(active_users),
            }
        )

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated and user.username in active_users:
            active_users.remove(user.username)  # ✅ remove user from active set

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Broadcast updated online count
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "online_count",
                "count": len(active_users),
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope["user"]
        text = data.get("text", "").strip()
        image_data = data.get("image")

        message = await self._save_message(user.id, text, image_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "username": user.username if user.is_authenticated else "Anon",
                "text": message["text"],
                "image_url": message["image_url"],
                "timestamp": message["timestamp"],  # <-- add this
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def online_count(self, event):
        # send online count update to client
        await self.send(text_data=json.dumps({
            "type": "online_count",
            "count": event["count"]
        }))

    @database_sync_to_async
    def _save_message(self, user_id, text, image_data):
        from .models import Message, CustomUser
        user = CustomUser.objects.filter(id=user_id).first()
        msg = Message(user=user, text=text)

        if image_data:
            fmt, imgstr = image_data.split(";base64,")
            ext = fmt.split("/")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            msg.image.save(filename, ContentFile(base64.b64decode(imgstr)), save=False)

        msg.save()
        return {
        "text": msg.text,
        "image_url": msg.image.url if msg.image else None,
        "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),  # formatted
    }

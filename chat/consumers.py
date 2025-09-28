# chat/consumers.py
import json
import base64
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f"group_{self.group_id}"
        # add to group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # optional: notify presence (client may request)
        # await self.channel_layer.group_send(...)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Expecting JSON payload with keys:
        - type: "message" | "seen" | "delete" | "typing"
        - message, reply_to (id), image (base64 data URL), message_id (for delete/seen)
        """
        if text_data is None:
            return
        data = json.loads(text_data)
        typ = data.get("type")

        if typ == "message":
            user = self.scope["user"]
            content = data.get("message", "").strip()
            reply_to = data.get("reply_to")  # id or None
            image_data = data.get("image")  # data URI or None

            msg = await self._save_message(user.id, content, reply_to, image_data)

            # broadcast new message
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "message": msg,
                }
            )

        elif typ == "seen":
            user = self.scope["user"]
            last_seen_id = data.get("last_seen_id")
            if last_seen_id:
                updated = await self._mark_seen_up_to(user.id, last_seen_id)
                # broadcast seen counts (you could send per-message updates or aggregated)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat.seen_update",
                        "updates": updated,  # list of {id, seen_count}
                    }
                )

        elif typ == "delete":
            user = self.scope["user"]
            message_id = data.get("message_id")
            if message_id:
                deleted = await self._delete_message_request(user.id, message_id)
                if deleted:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "chat.deleted",
                            "message_id": message_id,
                        }
                    )

        elif typ == "typing":
            user = self.scope["user"]
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.typing",
                    "user": user.username if user.is_authenticated else "Anon"
                }
            )
        
        elif typ == "audio":
            user = self.scope["user"]
            audio_data = data.get("audio")  # base64 data URL
            if audio_data:
                msg = await self._save_audio(user.id, audio_data)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat.audio",
                        "message": msg.to_dict(),  # include id, user, timestamp, audio_url
                    }
                )


    # Handlers for group_send events
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"type":"message", "message": event["message"]}))

    async def chat_deleted(self, event):
        await self.send(text_data=json.dumps({"type":"message_deleted", "message_id": event["message_id"]}))

    async def chat_seen_update(self, event):
        await self.send(text_data=json.dumps({"type":"seen_update", "updates": event["updates"]}))

    async def chat_typing(self, event):
        await self.send(text_data=json.dumps({"type":"typing", "user": event["user"]}))
        
    async def chat_audio(self, event):
        m = event["message"]
        await self.send(text_data=json.dumps({
            "type": "audio",
            "message": m
        }))

    # -------------- DB helpers -----------------
    @database_sync_to_async
    def _save_message(self, user_id, content, reply_to_id=None, image_data=None):
        from .models import Message, ChatGroup, CustomUser
        user = CustomUser.objects.get(id=user_id)
        group = ChatGroup.objects.get(id=self.group_id)
        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=int(reply_to_id))
            except Message.DoesNotExist:
                reply_to = None

        msg = Message(user=user, group=group, content=content, reply_to=reply_to)
        if image_data:
            # image_data expected like "data:image/png;base64,...."
            fmt, imgstr = image_data.split(";base64,")
            ext = fmt.split("/")[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            msg.image.save(filename, ContentFile(base64.b64decode(imgstr)), save=False)

        msg.save()
        return msg.to_dict()

    @database_sync_to_async
    def _mark_seen_up_to(self, user_id, last_seen_id):
        from .models import Message, CustomUser
        user = CustomUser.objects.get(id=user_id)
        msgs = Message.objects.filter(group_id=self.group_id, id__lte=last_seen_id)
        updates = []
        for m in msgs:
            # add user (idempotent)
            m.seen_by.add(user)
            # count updated value and append
            updates.append({"id": m.id, "seen_count": m.seen_by.count()})
        return updates

    @database_sync_to_async
    def _delete_message_request(self, user_id, message_id):
        """
        Allow delete if user is the message owner OR group admin.
        Return True if deleted.
        """
        from .models import Message, CustomUser
        user = CustomUser.objects.get(id=user_id)
        try:
            m = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return False

        # permission check
        if m.user_id == user.id or m.group.admin_id == user.id:
            m.delete()
            return True
        return False
    
    @database_sync_to_async
    def _save_audio(self, user_id, audio_data):
        from .models import Message, ChatGroup, CustomUser
        import base64, uuid
        from django.core.files.base import ContentFile

        user  = CustomUser.objects.get(id=user_id)
        group = ChatGroup.objects.get(id=self.group_id)

        # audio_data like: "data:audio/webm;base64,AAAA..."
        fmt, b64 = audio_data.split(';base64,')
        ext = fmt.split('/')[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        msg = Message(user=user, group=group)
        msg.audio.save(filename, ContentFile(base64.b64decode(b64)), save=True)
        return msg


# chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/chat/?$", consumers.ChatConsumer.as_asgi()),
]
# This file defines WebSocket routing for the chat application.
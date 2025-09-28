import os
import django
from django.core.asgi import get_asgi_application

# Set the default Django settings module FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatproj.settings')

# Initialize Django before importing anything that requires Django apps
django.setup()

# Now import Channels components
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
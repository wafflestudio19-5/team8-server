"""
ASGI config for wafflemarket project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""
import os

from channels.routing import ProtocolTypeRouter, URLRouter

from django.core.asgi import get_asgi_application

import chat.routing
from wafflemarket.middleware import JwtAuthMiddleware


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wafflemarket.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": JwtAuthMiddleware(URLRouter(chat.routing.websocket_urlpatterns)),
    }
)

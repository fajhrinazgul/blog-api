import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog_api.settings")
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

django_asgi_app = get_asgi_application()

# Import setelah django_asgi_app untuk menghindari AppRegistryNotReady
from chat.middleware import JWTAuthMiddleware
import chat.routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(URLRouter(chat.routing.websocket_urlpatterns)),
    }
)

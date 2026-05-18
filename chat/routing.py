from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Mencocokkan url ws://domain/ws/chat/nama-room-slug/
    re_path(r"^ws/chat/(?P<room_slug>[\w-]+)/$", consumers.ChatConsumer.as_asgi()),
]

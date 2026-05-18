from django.urls import path
from .views import (
    RoomListCreateAPIView,
    RoomRetrieveUpdateDestroyAPIView,
    ChatMessageListAPIView,
)

urlpatterns = [
    path("api/chat/rooms/", RoomListCreateAPIView.as_view(), name="room-list-create"),
    path(
        "api/chat/rooms/<str:slug>/",
        RoomRetrieveUpdateDestroyAPIView.as_view(),
        name="room-detail-update-destroy",
    ),
    path(
        "api/chat/rooms/<str:room_slug>/messages/",
        ChatMessageListAPIView.as_view(),
        name="room-chat-messages",
    ),
]

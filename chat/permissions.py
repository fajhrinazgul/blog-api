from rest_framework import permissions
from .models import Room


class IsRoomAdminOrReadOnly(permissions.BasePermission):
    """
    Permission khusus:
    - Member room hanya bisa melihat (GET) detail room.
    - Hanya Admin Room yang bisa edit (PUT/PATCH) atau hapus (DELETE).
    """

    def has_object_permission(self, request, view, obj):
        # Jika request adalah GET, HEAD, atau OPTIONS (Read-Only)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Jika request adalah PUT, PATCH, atau DELETE, cek apakah dia adminnya
        return obj.admin == request.user


class IsRoomMemberForChat(permissions.BasePermission):
    """
    Permission untuk memastikan user hanya bisa melihat riwayat chat
    jika mereka terdaftar sebagai member di room tersebut.
    """

    def has_permission(self, request, view):
        # Ambil room_slug dari parameter URL (misal: /api/chat/rooms/<room_slug>/messages/)
        room_slug = view.kwargs.get("room_slug")

        # Cek apakah room ada dan user adalah salah satu membernya
        return Room.objects.filter(slug=room_slug, members=request.user).exists()

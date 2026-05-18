from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Room
from .serializers import RoomSerializer
from .permissions import IsRoomAdminOrReadOnly  # Import permission baru
from .models import Chat
from .serializers import ChatSerializer
from .permissions import IsRoomMemberForChat
from users.paginations import CustomLimitOffsetPagination


# View ListCreate tetap sama seperti sebelumnya
class RoomListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Room.objects.filter(members=self.request.user).order_by("name")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Room berhasil dibuat.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


# UBAH KELAS INI
class RoomRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Detail Room (Bisa diakses seluruh member room)
    PUT/PATCH: Edit Room / Kelola Anggota (Hanya Admin Room)
    DELETE: Hapus Room (Hanya Admin Room)
    """

    serializer_class = RoomSerializer
    lookup_field = "slug"
    # Gabungkan IsAuthenticated dan Custom Permission kita
    permission_classes = [permissions.IsAuthenticated, IsRoomAdminOrReadOnly]

    def get_queryset(self):
        # Memastikan user luar tidak bisa melihat/mengakses room ini sama sekali
        return Room.objects.filter(members=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"message": "Detail room berhasil dimuat.", "data": serializer.data}
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {"message": "Room berhasil diperbarui.", "data": serializer.data}
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Room berhasil dihapus."}, status=status.HTTP_200_OK
        )


class ChatMessageListAPIView(generics.ListAPIView):
    """
    GET: Mengambil riwayat percakapan di dalam room berdasarkan `room_slug`.
         Hanya bisa diakses oleh user yang menjadi member room tersebut.
    """

    serializer_class = ChatSerializer
    pagination_class = CustomLimitOffsetPagination
    # Gabungkan pengecekan: Harus login DAN harus member room
    permission_classes = [permissions.IsAuthenticated, IsRoomMemberForChat]

    def get_queryset(self):
        room_slug = self.kwargs.get("room_slug")
        # Ambil semua chat berdasarkan slug room, diurutkan dari yang paling baru (terkini)
        return Chat.objects.filter(room__slug=room_slug).order_by("-timestamp")

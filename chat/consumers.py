import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Chat
from .serializers import ChatSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_slug = self.scope["url_route"]["kwargs"]["room_slug"]
        self.room_group_name = f"chat_{self.room_slug}"
        self.user = self.scope.get("user")

        # 1. Validasi Autentikasi dari Middleware
        if not self.user or self.user.is_anonymous:
            await self.close(code=4001)  # Tutup koneksi jika tidak terautentikasi
            return

        # 2. Validasi apakah Room ada dan User adalah member dari room tersebut
        if not await self.is_room_member(self.room_slug, self.user):
            await self.close(code=4003)  # Forbidden jika bukan member room
            return

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # [BARU] Begitu user TERKONEKSI (membuka chat), otomatis tandai pesan lama sebagai TERBACA
        await self.mark_room_as_read()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    # Menerima pesan dari WebSocket (Client -> Server)
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action", "send_message")

            # Jika action adalah mengirim pesan
            if action == "send_message":
                message_content = data.get("message", "").strip()
                if not message_content:
                    return

                chat_data = await self.save_message(
                    self.room_slug, self.user, message_content
                )

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {"type": "chat_message", "message_data": chat_data},
                )
            # LOGIKA 2: Jika action-nya adalah menandai pesan terbaca (misal dipicu saat user scroll ke bawah)
            elif action == "read_messages":
                await self.mark_room_as_read()

        except Exception as e:
            import traceback

            print("WEBSOCKET RECEIVE ERROR:", str(e))
            traceback.print_exc()  # Ini akan memunculkan baris error di terminal terminal Django Anda

    # Menerima pesan dari group room (Server -> Client)
    async def chat_message(self, event):
        message_data = event["message_data"]

        # Kirim pesan asli ke WebSocket Client dalam format JSON
        await self.send(text_data=json.dumps(message_data))

    # [BARU] Handler untuk memberi tahu client lain bahwa pesan telah dibaca
    async def messages_read_notification(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "action": "messages_read",
                    "reader_id": event["reader_id"],
                    "room_slug": self.room_slug,
                }
            )
        )

    # --- DATABASE METHODS (Harus Sync) ---

    # 1. Ini fungsi utama asinkron (Berjalan di thread utama yang punya event loop)
    async def mark_room_as_read(self):
        """Menandai semua pesan dari orang lain sebagai terbaca"""
        # Panggil fungsi DB dan tunggu hasilnya (True jika ada pesan yang di-update)
        has_updated = await self._update_messages_in_db()

        # Jika ada pesan yang berhasil di-update, lakukan broadcast dari sini
        if has_updated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "messages_read_notification", "reader_id": self.user.id},
            )

    # 2. Ini fungsi database murni (Dipisah, tanpa ada kode async di dalamnya)
    @database_sync_to_async
    def _update_messages_in_db(self):
        """Murni melakukan query ORM Django untuk update data"""
        unread_chats = Chat.objects.filter(
            room__slug=self.room_slug, is_read=False
        ).exclude(sender=self.user)

        if unread_chats.exists():
            unread_chats.update(is_read=True)
            return True  # Beritahu fungsi utama kalau ada yang di-update

        return False  # Tidak ada pesan baru yang perlu ditandai

    @database_sync_to_async
    def is_room_member(self, slug, user):
        """Memastikan room ada dan user terdaftar di dalam room tersebut"""
        try:
            room = Room.objects.get(slug=slug)
            return room.members.filter(id=user.id).exists()
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, slug, user, content):
        try:
            # Cari room murni berdasarkan slug
            room = Room.objects.get(slug=slug)

            # Buat objek chat
            chat = Chat.objects.create(
                room=room,
                sender=user,  # Ini adalah user member yang sedang terkoneksi
                content=content,
            )

            serializer = ChatSerializer(chat)
            return serializer.data
        except Exception as e:
            print("ERROR DI SAVE MESSAGE:", str(e))
            raise e

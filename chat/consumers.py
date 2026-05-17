# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .serializers import MessageSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.me = self.scope["user"]
        print(self.me)
        # Cek apakah user sudah terautentikasi (via middleware)
        if self.me.is_anonymous:
            await self.close()
            return

        # Mengambil ID lawan bicara dari URL (misal: /ws/chat/12/)
        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]

        # Logika mengurutkan ID untuk nama Room yang unik
        user_ids = sorted([int(self.me.id), int(self.other_user_id)])
        self.room_group_name = f"chat_{user_ids[0]}_{user_ids[1]}"

        # Gabung ke room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name") and self.channel_layer:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    # Menerima pesan dari WebSocket (Client)
    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("content")

        if content:
            # Simpan ke database secara asynchronous
            message_data = await self.save_message(
                self.me.id, self.other_user_id, content
            )

            # Kirim pesan ke group room agar user lawan menerima
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat_message", "message": message_data}
            )

    # Handler untuk event 'chat_message'
    async def chat_message(self, event):
        message = event["message"]

        # Kirim data ke client (browser/aplikasi mobile)
        await self.send(text_data=json.dumps(message))

    # Helper untuk menyimpan pesan menggunakan DRF Serializer di thread terpisah
    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        data = {"sender": sender_id, "receiver": receiver_id, "content": content}
        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return serializer.data
        return {"error": "Invalid data"}

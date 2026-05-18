from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Room, Chat

User = get_user_model()


class UserMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class RoomSerializer(serializers.ModelSerializer):
    admin = UserMinifiedSerializer(read_only=True)
    members = UserMinifiedSerializer(many=True, read_only=True)

    # Gunakan member_ids untuk input/edit daftar ID anggota (termasuk saat mengeluarkan anggota)
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="members",
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Room
        fields = ["id", "name", "slug", "admin", "members", "member_ids"]
        read_only_fields = ["id", "admin"]

    def create(self, validated_data):
        request = self.context.get("request")
        current_user = request.user

        members_data = validated_data.pop("members", [])

        # Otomatis set admin ke user yang sedang login
        room = Room.objects.create(admin=current_user, **validated_data)

        # Otomatis pastikan admin masuk ke list members
        room.members.add(current_user)

        # Tambahkan anggota lainnya
        for user in members_data:
            room.members.add(user)

        return room

    def update(self, instance, validated_data):
        # Jika ada input 'member_ids', DRF otomatis mengonversinya menjadi list user karena 'source=members'
        if "members" in validated_data:
            members_data = validated_data.pop("members")

            # Pasang list member baru (ini akan menggantikan list lama)
            instance.members.set(members_data)

            # Pastikan admin TIDAK BISA mengeluarkan dirinya sendiri secara tidak sengaja
            if instance.admin not in instance.members.all():
                instance.members.add(instance.admin)

        return super().update(instance, validated_data)


class ChatSerializer(serializers.ModelSerializer):
    sender = UserMinifiedSerializer(read_only=True)
    room_slug = serializers.CharField(source="room.slug", read_only=True)

    class Meta:
        model = Chat
        fields = ["id", "room_slug", "sender", "content", "is_read", "timestamp"]

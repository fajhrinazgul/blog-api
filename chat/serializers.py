from rest_framework import serializers

from chat.models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source="sender.username")
    receiver_username = serializers.ReadOnlyField(source="receiver.username")

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "sender_username",
            "receiver",
            "receiver_username",
            "content",
            "timestamp",
            "is_read",
        ]

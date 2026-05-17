from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Message
from .serializers import MessageSerializer
from django.db.models import Q


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, other_user_id):
        messages = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver_id=other_user_id))
            | (Q(sender_id=other_user_id) & Q(receiver=request.user))
        )
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

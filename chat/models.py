from django.db import models
from django.conf import settings

AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "users.User")


class Message(models.Model):
    sender = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return (
            f"{self.sender.username} to {self.receiver.username}: {self.content[:20]}"
        )

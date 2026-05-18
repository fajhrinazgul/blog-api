from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "users.User")


class Room(models.Model):
    name = models.CharField(_("name"), max_length=30, unique=True)
    slug = models.CharField(unique=True)
    members = models.ManyToManyField(AUTH_USER_MODEL, related_name="room_members")
    admin = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="room_admins"
    )

    def __str__(self):
        return self.name


class Chat(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="chats")
    sender = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chatsenders"
    )
    content = models.TextField(_("content"))
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room.name} - {self.pk} - {self.sender.username}"

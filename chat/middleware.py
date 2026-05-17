# chat/channels_middleware.py
from channels.db import database_sync_to_async
from users.models import User
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs


@database_sync_to_async
def get_user_from_token(token_key):
    try:
        # Validasi token JWT
        access_token = AccessToken(token_key)
        print(access_token["user_id"])
        user_id = access_token["user_id"]
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Tutup koneksi database yang usang
        close_old_connections()

        # Ambil token dari query string url (?token=xxx)
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token")

        if token:
            scope["user"] = await get_user_from_token(token[0])
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)

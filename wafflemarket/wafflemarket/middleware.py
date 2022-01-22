from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.forms import ValidationError
from rest_framework.authtoken.models import Token
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections

@database_sync_to_async
def get_user_from_token(token):
    try:
        valid_data = VerifyJSONWebTokenSerializer().validate({"token": token})
        return valid_data['user']
    except:
        return None


class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections()
        headers = dict(scope['headers'])
        if b'authorization' in headers:
            try:
                token_name, token_key = headers[b'authorization'].decode().split()
                if token_name == 'JWT':
                    scope['user'] = await get_user_from_token(token_key)
            except ValueError:
                return None
        if scope['user'] is None:
            return None
        return await super().__call__(scope, receive, send)

def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))

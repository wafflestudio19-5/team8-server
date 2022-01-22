from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework import status
from rest_framework.response import Response
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer

from django.db import close_old_connections


@database_sync_to_async
def get_user_from_token(token):
    try:
        valid_data = VerifyJSONWebTokenSerializer().validate({"token": token})
        return valid_data["user"]
    except:
        return None


class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections()

        # find JWT token and authorize
        headers = dict(scope["headers"])
        if b"authorization" in headers:
            try:
                token_name, token_key = headers[b"authorization"].decode().split()
                if token_name == "JWT":
                    scope["user"] = await get_user_from_token(token_key)
            except:
                return Response("인증에 실패하였습니다.", status=status.HTTP_401_UNAUTHORIZED)

        # if token is not valid
        if scope["user"] is None:
            return Response("인증에 실패하였습니다.", status=status.HTTP_401_UNAUTHORIZED)
        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))

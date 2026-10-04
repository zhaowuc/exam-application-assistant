from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from rest_framework.throttling import AnonRateThrottle


class VersionedAuthentication(JWTAuthentication):
    def get_user(self, token):
        user = super().get_user(token)
        if user.status != 'active' or token.get('auth_version') != user.auth_version:
            raise AuthenticationFailed('登录已失效，请重新登录。')
        return user


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == 'admin' and request.user.status == 'active')


class LoginThrottle(AnonRateThrottle):
    rate = '15/min'


class RegisterThrottle(AnonRateThrottle):
    rate = '10/hour'

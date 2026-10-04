from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from . import models as m
from .serializers import UserSerializer, model_serializer
from .security import LoginThrottle, RegisterThrottle


def tokens(user):
    token = RefreshToken.for_user(user)
    token['auth_version'] = user.auth_version
    return {'access':str(token.access_token),'refresh':str(token),'user':UserSerializer(user).data}


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login(request):
    user = authenticate(username=request.data.get('username',''), password=request.data.get('password',''))
    if not user or user.status != 'active':
        raise AuthenticationFailed('用户名或密码错误，或账号已被停用。')
    return Response(tokens(user))


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterThrottle])
@transaction.atomic
def register(request):
    data = {key:request.data.get(key,'') for key in ['username','password','email','phone']}
    validate_password(data['password'])
    serializer = UserSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save(role='user', status='active')
    m.UserProfile.objects.create(user=user)
    return Response(tokens(user), status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh(request):
    try:
        token = RefreshToken(request.data.get('refresh',''))
        user = m.User.objects.get(pk=token['user_id'], status='active')
        if token.get('auth_version') != user.auth_version:
            raise ValueError('revoked')
        token.blacklist()
        return Response(tokens(user))
    except Exception:
        raise AuthenticationFailed('登录已过期，请重新登录。')


@api_view(['GET','PATCH'])
def me(request):
    if request.method == 'PATCH':
        serializer = UserSerializer(request.user, data={key:value for key,value in request.data.items() if key in ['email','phone']}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
def logout(request):
    request.user.auth_version += 1
    request.user.save(update_fields=['auth_version'])
    return Response({'logged_out':True})


@api_view(['POST'])
def change_password(request):
    if not request.user.check_password(request.data.get('old_password','')):
        raise ValidationError({'old_password':'原密码不正确。'})
    password = request.data.get('new_password','')
    validate_password(password, request.user)
    request.user.set_password(password)
    request.user.auth_version += 1
    request.user.save()
    return Response({'message':'密码已修改，请重新登录。'})


@api_view(['GET','PATCH','PUT'])
def profile(request):
    obj, _ = m.UserProfile.objects.get_or_create(user=request.user)
    cls = model_serializer(m.UserProfile, read_only=('user',))
    if request.method != 'GET':
        serializer = cls(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        year = serializer.validated_data.get('birth_year')
        if year and not 1900 <= year <= __import__('django').utils.timezone.now().year:
            raise ValidationError({'birth_year':'出生年份不合理。'})
        for key in ['certificates','target_regions','target_unit_types','school_preferences']:
            if key in serializer.validated_data and not isinstance(serializer.validated_data[key],list):
                raise ValidationError({key:'应为数组。'})
        if 'mock_scores' in serializer.validated_data:
            value = serializer.validated_data['mock_scores']
            if not isinstance(value,dict) or any(not isinstance(v,(int,float)) or not 0<=v<=1000 for v in value.values()):
                raise ValidationError({'mock_scores':'应为各考试类型与数值分数的对象。'})
        serializer.save()
    return Response(cls(obj).data)

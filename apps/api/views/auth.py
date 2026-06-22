from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from apps.api.serializers.auth import RegisterSerializer, LoginSerializer, UserSerializer


def set_auth_cookies(response, access_token, refresh_token):
    secure = getattr(settings, 'JWT_AUTH_COOKIE_SECURE', True)
    samesite = getattr(settings, 'JWT_AUTH_COOKIE_SAMESITE', 'Lax')
    response.set_cookie(
        key=settings.JWT_AUTH_COOKIE,
        value=str(access_token),
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=3600,
    )
    response.set_cookie(
        key=settings.JWT_AUTH_REFRESH_COOKIE,
        value=str(refresh_token),
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=7 * 24 * 3600,
    )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response({
            'user': UserSerializer(user).data,
            'message': 'Account created successfully.'
        }, status=status.HTTP_201_CREATED)
        set_auth_cookies(response, refresh.access_token, refresh)
        return response


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        response = Response({
            'user': UserSerializer(user).data,
            'message': 'Logged in successfully.'
        })
        set_auth_cookies(response, refresh.access_token, refresh)
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass
        response = Response({'message': 'Logged out successfully.'})
        response.delete_cookie(settings.JWT_AUTH_COOKIE)
        response.delete_cookie(settings.JWT_AUTH_REFRESH_COOKIE)
        return response


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if not refresh_token:
            return Response({'error': 'No refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token
            response = Response({'message': 'Token refreshed.'})
            response.set_cookie(
                key=settings.JWT_AUTH_COOKIE,
                value=str(access_token),
                httponly=True,
                secure=getattr(settings, 'JWT_AUTH_COOKIE_SECURE', True),
                samesite=getattr(settings, 'JWT_AUTH_COOKIE_SAMESITE', 'Lax'),
                max_age=3600,
            )
            return response
        except TokenError:
            return Response(
                {'error': 'Invalid or expired refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

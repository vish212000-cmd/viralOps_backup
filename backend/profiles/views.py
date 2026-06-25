import secrets
from django.utils import timezone
from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import update_session_auth_hash
from rest_framework_simplejwt.tokens import OutstandingToken, BlacklistedToken
from .models import APIToken, SessionHistory, ConnectedAccounts
from .serializers import (
    FullAccountSerializer, APITokenSerializer,
    SessionHistorySerializer, ConnectedAccountsSerializer
)

class AccountViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        serializer = FullAccountSerializer(request.user)
        return Response(serializer.data)

    def create(self, request):
        # We use create/post to update the user account data.
        serializer = FullAccountSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post', 'delete'], parser_classes=[MultiPartParser, FormParser])
    def avatar(self, request):
        profile = request.user.profile
        if request.method == 'DELETE':
            if profile.avatar:
                profile.avatar.delete(save=False)
                profile.avatar = None
                profile.save()
            return Response({"status": "Avatar deleted"}, status=status.HTTP_200_OK)
            
        # POST/PATCH for upload
        avatar_file = request.FILES.get('avatar')
        if not avatar_file:
            return Response({"error": "No avatar file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation is done on client, but we can do basic here
        if avatar_file.size > 5 * 1024 * 1024:
            return Response({"error": "File too large. Maximum 5MB."}, status=status.HTTP_400_BAD_REQUEST)
            
        if profile.avatar:
            profile.avatar.delete(save=False)
            
        profile.avatar = avatar_file
        profile.save()
        return Response({"status": "Avatar updated", "avatar_url": request.build_absolute_uri(profile.avatar.url)}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not current_password or not new_password:
            return Response({"error": "current_password and new_password are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        if not user.check_password(current_password):
            return Response({"error": "Incorrect current password"}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        
        # Keep user logged in after password change (optional, but good UX if using session auth)
        update_session_auth_hash(request, user)
        
        # Update security settings
        security_settings = user.security_settings
        security_settings.last_password_change = timezone.now()
        security_settings.save()
        
        return Response({"status": "Password changed successfully"}, status=status.HTTP_200_OK)


class APITokenViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = APITokenSerializer

    def get_queryset(self):
        return APIToken.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        name = request.data.get('name')
        if not name:
            return Response({"error": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        raw_token = f"vo_{secrets.token_urlsafe(32)}"
        token = APIToken(user=request.user, name=name, scopes=request.data.get('scopes', []))
        token.set_token(raw_token)
        token.save()
        
        # We only return the raw token once!
        serializer = self.get_serializer(token)
        data = serializer.data
        data['raw_token'] = raw_token
        return Response(data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'])
    def rotate(self, request, pk=None):
        token = self.get_object()
        raw_token = f"vo_{secrets.token_urlsafe(32)}"
        token.set_token(raw_token)
        token.save()
        
        serializer = self.get_serializer(token)
        data = serializer.data
        data['raw_token'] = raw_token
        return Response(data, status=status.HTTP_200_OK)


class SessionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SessionHistorySerializer

    def get_queryset(self):
        return SessionHistory.objects.filter(user=self.request.user).order_by('-last_activity')

    def _blacklist_token_by_jti(self, jti):
        # Finds the OutstandingToken and adds it to BlacklistedToken
        try:
            outstanding = OutstandingToken.objects.get(jti=jti)
            BlacklistedToken.objects.get_or_create(token=outstanding)
        except OutstandingToken.DoesNotExist:
            pass

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        session = self.get_object()
        session.terminate()
        self._blacklist_token_by_jti(session.session_id)
        return Response({"status": "Session revoked"})

    @action(detail=False, methods=['post'])
    def revoke_all_others(self, request):
        current_jti = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            from rest_framework_simplejwt.tokens import UntypedToken
            try:
                token_obj = UntypedToken(auth_header.split(' ')[1])
                current_jti = token_obj.get('jti')
            except Exception:
                pass

        # Revoke sessions
        other_sessions = SessionHistory.objects.filter(user=request.user, is_active=True)
        if current_jti:
            other_sessions = other_sessions.exclude(session_id=current_jti)
            
        for sess in other_sessions:
            sess.terminate()
            self._blacklist_token_by_jti(sess.session_id)
            
        return Response({"status": "All other sessions revoked"})


class ConnectedAccountsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ConnectedAccountsSerializer

    def get_queryset(self):
        return ConnectedAccounts.objects.filter(user=self.request.user)

from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache

class HealthzView(views.APIView):
    """Simple heartbeat check (liveness)"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({'status': 'UP'}, status=status.HTTP_200_OK)

class ReadyView(views.APIView):
    """Service connection readiness check (readiness)"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # 1. Database Check
        try:
            connection.ensure_connection()
        except Exception as e:
            return Response({
                'status': 'DOWN',
                'service': 'database',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # 2. Redis/Cache Check
        try:
            cache.set('ready_check', 'ok', 5)
            if cache.get('ready_check') != 'ok':
                return Response({
                    'status': 'DOWN',
                    'service': 'cache_redis',
                    'error': 'Write/read value mismatch'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'status': 'DOWN',
                'service': 'cache_redis',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response({'status': 'READY'}, status=status.HTTP_200_OK)

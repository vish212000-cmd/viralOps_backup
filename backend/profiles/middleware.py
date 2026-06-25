import logging
from django.utils import timezone
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import SessionHistory
from django.core.cache import cache

logger = logging.getLogger(__name__)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class SessionTrackingMiddleware:
    """
    Middleware to track user sessions. 
    It parses the JWT from the Authorization header, extracts the JTI,
    and updates the SessionHistory's last_activity timestamp.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only run on successful API responses to avoid overhead on 404s/401s
        if response.status_code >= 400:
            return response

        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token_string = auth_header.split(' ')[1]
            try:
                # We decode the token without verifying the DB (fast)
                token = UntypedToken(token_string)
                jti = token.get('jti')
                user_id = token.get('user_id')

                if jti and user_id:
                    # Debounce DB updates using cache (e.g. update at most once every 5 minutes per session)
                    cache_key = f"session_active_{jti}"
                    if not cache.get(cache_key):
                        ip = get_client_ip(request)
                        user_agent = request.headers.get('User-Agent', '')[:255]
                        
                        # We use get_or_create to ensure the session exists, 
                        # in case the login view didn't create it explicitly.
                        session, created = SessionHistory.objects.get_or_create(
                            session_id=jti,
                            defaults={
                                'user_id': user_id,
                                'ip_address': ip,
                                'browser': user_agent,  # simplified
                                'is_active': True,
                            }
                        )
                        if not created:
                            # Update existing
                            session.ip_address = ip
                            session.browser = user_agent
                            session.last_activity = timezone.now()
                            session.save(update_fields=['ip_address', 'browser', 'last_activity'])
                        
                        cache.set(cache_key, True, 300) # 5 minutes debounce

            except (InvalidToken, TokenError) as e:
                pass
            except Exception as e:
                logger.error(f"SessionTrackingMiddleware error: {str(e)}")

        return response

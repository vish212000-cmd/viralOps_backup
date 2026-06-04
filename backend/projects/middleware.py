import time
from django.utils.deprecation import MiddlewareMixin
from .metrics import API_REQUESTS, API_LATENCY

class PrometheusCustomMetricsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        if not hasattr(request, '_start_time'):
            return response
            
        latency = time.time() - request._start_time
        
        # Determine clean path/endpoint to prevent high cardinality
        path = request.path
        parts = path.split('/')
        if len(parts) > 3 and parts[1] == 'api' and parts[2] == 'orgs':
            # Group orgs/:org_slug/
            parts[3] = ':org_slug'
            if len(parts) > 5 and parts[5].isdigit():
                parts[5] = ':id'
            if len(parts) > 7 and parts[7].isdigit():
                parts[7] = ':id'
            endpoint = "/".join(parts)
        else:
            # Group numeric IDs in other endpoints
            for idx, part in enumerate(parts):
                if part.isdigit():
                    parts[idx] = ':id'
            endpoint = "/".join(parts)
            
        method = request.method
        status_code = str(response.status_code)
        
        # Extract Tenant from Header (Casing checks for wsgi standards)
        tenant_id = request.headers.get('X-Org-Slug') or request.META.get('HTTP_X_ORG_SLUG') or 'anonymous'
        
        API_LATENCY.labels(endpoint=endpoint, method=method).observe(latency)
        API_REQUESTS.labels(endpoint=endpoint, method=method, status_code=status_code, tenant_id=tenant_id).inc()
        
        return response

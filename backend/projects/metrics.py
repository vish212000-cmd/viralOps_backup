from prometheus_client import Counter, Histogram, Gauge

# Request counters (tagged by endpoint + tenant)
API_REQUESTS = Counter(
    'viralops_api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status_code', 'tenant_id']
)

# Response time histogram
API_LATENCY = Histogram(
    'viralops_api_request_latency_seconds',
    'API request latency',
    ['endpoint', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Tenant-specific gauges
ACTIVE_TENANTS = Gauge('viralops_active_tenants', 'Number of active tenants')
CELERY_TASKS_QUEUED = Gauge('viralops_celery_tasks_queued', 'Tasks in Celery queue')
CELERY_TASKS_PROCESSING = Gauge('viralops_celery_tasks_processing', 'Tasks being processed')

# Billing metrics
SUBSCRIPTIONS_ACTIVE = Gauge('viralops_subscriptions_active', 'Active subscriptions', ['plan'])
REVENUE_MRR = Gauge('viralops_revenue_mrr', 'Monthly recurring revenue (INR)')

# AI/Generation metrics
AI_GENERATIONS_TOTAL = Counter(
    'viralops_ai_generations_total',
    'Total AI generations',
    ['asset_type', 'tenant_id']
)

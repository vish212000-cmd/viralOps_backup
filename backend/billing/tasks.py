import logging
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Subscription

logger = logging.getLogger(__name__)

@shared_task
def check_expired_subscriptions():
    """
    Runs daily to mark active subscriptions past their end date as PAST_DUE.
    """
    now = timezone.now()
    expired_subs = Subscription.objects.filter(status='ACTIVE', current_period_end__lt=now)
    count = expired_subs.count()
    
    if count > 0:
        for sub in expired_subs:
            sub.status = 'PAST_DUE'
            sub.save()
            logger.info(f"Marked subscription {sub.id} for tenant {sub.tenant.name} as PAST_DUE.")
        logger.info(f"Completed check_expired_subscriptions: updated {count} subscriptions.")
    else:
        logger.info("check_expired_subscriptions: No expired subscriptions found.")
    return count

@shared_task
def send_payment_reminder():
    """
    Runs daily to notify users whose subscriptions renew in 3 days.
    """
    now = timezone.now()
    three_days_from_now_start = now + timezone.timedelta(days=3)
    three_days_from_now_end = three_days_from_now_start + timezone.timedelta(days=1)
    
    reminder_subs = Subscription.objects.filter(
        status='ACTIVE',
        current_period_end__range=(three_days_from_now_start, three_days_from_now_end)
    )
    count = reminder_subs.count()
    
    for sub in reminder_subs:
        try:
            send_mail(
                subject="Subscription Renewal Reminder - ViralOps",
                message=f"Hello, this is a reminder that your ViralOps {sub.plan.get_name_display()} subscription will renew in 3 days on {sub.current_period_end.strftime('%Y-%m-%d')}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[sub.user.email],
                fail_silently=False
            )
            logger.info(f"Sent payment renewal reminder to {sub.user.email} for subscription {sub.id}.")
        except Exception as e:
            logger.error(f"Failed to send renewal reminder email to {sub.user.email}: {str(e)}")
            
    logger.info(f"Completed send_payment_reminder: processed {count} reminders.")
    return count

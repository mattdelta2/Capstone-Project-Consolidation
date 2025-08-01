# news/api/signals.py

import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from news.models import Article
from django.core.mail import send_mail
from django.conf import settings


@receiver(post_save, sender=Article)
def api_article_approved(sender, instance, created, **kwargs):
    # when status flips to APPROVED, notify:
    if instance.status == Article.STATUS_APPROVED:
        # broadcast via email (your real code might loop subscribers)
        send_mail(
            subject=f"New Article: {instance.title}",
            message=instance.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[u.email for u in instance.publisher.subscribers.all()],
            fail_silently=True,
        )
        # and post to X
        requests.post("https://api.x.com/statuses/update", 
                      data={"status": instance.title})

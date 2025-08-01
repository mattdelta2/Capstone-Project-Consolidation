# news/signals.py

from django.conf import settings
from django.core.mail import send_mass_mail
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Article, Newsletter


# -----------------------------------------------------------------------------
# Article approval caching & notifications
# -----------------------------------------------------------------------------
@receiver(pre_save, sender=Article)
def cache_previous_article_approval(sender, instance, **kwargs):
    if not instance.pk:
        instance._was_approved = False
    else:
        old_status = (
            Article.objects
            .filter(pk=instance.pk)
            .values_list("status", flat=True)
            .first()
        )
        instance._was_approved = (old_status == Article.STATUS_APPROVED)


@receiver(post_save, sender=Article)
def send_article_notifications(sender, instance, created, **kwargs):
    # Only fire when an existing article is freshly approved
    if created or instance.status != Article.STATUS_APPROVED or instance._was_approved:
        return

    # Gather subscribers
    pub_subs = instance.publisher.subscribers.all()
    journ_subs = instance.author.subscriber_set.all()
    recipients = set(pub_subs) | set(journ_subs)

    # Build email messages
    messages = []
    for user in recipients:
        subject = f"New Article Published: {instance.title}"
        preview = instance.body[:200] + ("…" if len(instance.body) > 200 else "")
        from_email = settings.DEFAULT_FROM_EMAIL
        to_list = [user.email]
        messages.append((subject, preview, from_email, to_list))

    # Send emails
    try:
        send_mass_mail(tuple(messages), fail_silently=True)
        print(f"[EMAIL] Sent {len(messages)} article notifications.")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")

    # Simulate tweet to X
    token = getattr(settings, "X_API_BEARER_TOKEN", None)
    if token:
        print(f"[X SIMULATION] Would post tweet: Article - {instance.title}")
    else:
        print("[X SIMULATION] No X_API_BEARER_TOKEN; skipping tweet.")


# -----------------------------------------------------------------------------
# Newsletter approval caching & notifications
# -----------------------------------------------------------------------------
@receiver(pre_save, sender=Newsletter)
def cache_previous_newsletter_approval(sender, instance, **kwargs):
    if not instance.pk:
        instance._was_approved = False
    else:
        old_status = (
            Newsletter.objects
                      .filter(pk=instance.pk)
                      .values_list("status", flat=True)
                      .first()
        )
        instance._was_approved = (old_status == Newsletter.STATUS_APPROVED)


@receiver(post_save, sender=Newsletter)
def send_newsletter_notifications(sender, instance, created, **kwargs):
    # Only fire when an existing newsletter is freshly approved
    if created or instance.status != \
     Newsletter.STATUS_APPROVED or instance._was_approved:
        return

    # Gather subscribers
    pub_subs = instance.publisher.subscribers.all() if instance.publisher else []
    journ_subs = instance.author.subscriber_set.all()
    recipients = set(pub_subs) | set(journ_subs)

    # Build email messages
    messages = []
    for user in recipients:
        subject = f"New Newsletter: {instance.title}"
        preview = instance.body[:200] + ("…" if len(instance.body) > 200 else "")
        from_email = settings.DEFAULT_FROM_EMAIL
        to_list = [user.email]
        messages.append((subject, preview, from_email, to_list))

    # Send emails
    try:
        send_mass_mail(tuple(messages), fail_silently=True)
        print(f"[EMAIL] Sent {len(messages)} newsletter notifications.")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")

    # Simulate tweet to X
    token = getattr(settings, "X_API_BEARER_TOKEN", None)
    if token:
        print(f"[X SIMULATION] Would post tweet: Newsletter - {instance.title}")
    else:
        print("[X SIMULATION] No X_API_BEARER_TOKEN; skipping tweet.")

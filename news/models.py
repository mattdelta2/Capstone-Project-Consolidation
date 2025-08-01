# news/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.conf import settings


class CustomUser(AbstractUser):
    ROLE_READER = 'reader'
    ROLE_JOURNALIST = 'journalist'
    ROLE_EDITOR = 'editor'

    ROLE_CHOICES = [
        (ROLE_READER, 'Reader'),
        (ROLE_JOURNALIST, 'Journalist'),
        (ROLE_EDITOR, 'Editor'),
    ]

    role = models.CharField(
        max_length=12,
        choices=ROLE_CHOICES,
        default=ROLE_READER,
    )

    # Which publishers this user follows
    subscriptions_publishers = models.ManyToManyField(
        'Publisher',
        blank=True,
        related_name='subscribers',
        help_text='Publishers you follow'
    )

    # Which journalists this user follows
    subscriptions_journalists = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='subscriber_set',
        help_text='Journalists you follow'
    )

    def is_reader(self):
        return self.role == self.ROLE_READER

    def is_journalist(self):
        return self.role == self.ROLE_JOURNALIST

    def is_editor(self):
        return self.role == self.ROLE_EDITOR

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Publisher(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    editors = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name='publisher_editor_set'
    )
    journalists = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name='publisher_journalist_set'
    )

    class Meta:
        verbose_name_plural = 'Publishers'

    def __str__(self):
        return self.name


class Article(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_DENIED = 'DENIED'

    STATUS_CHOICES = [
        (STATUS_PENDING,  'Pending review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_DENIED,   'Denied'),
    ]

    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name='articles'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='articles'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_approved(self):
        return self.status == self.STATUS_APPROVED

    def get_absolute_url(self):
        return reverse('news:article-detail', args=[self.pk])


class Newsletter(models.Model):
    STATUS_PENDING = "P"
    STATUS_APPROVED = "A"
    STATUS_DENIED = "D"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_DENIED, "Denied"),
    ]

    title = models.CharField(max_length=255)
    body = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": CustomUser.ROLE_JOURNALIST}
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

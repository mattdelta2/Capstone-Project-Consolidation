# news/models.py

"""
Defines the core data models for the News Portal application, including:
- CustomUser: extends Django’s user with roles and follow relationships.
- Publisher: represents media outlets and their staff.
- Article: news articles written by users.
- Newsletter: periodic newsletters authored by journalists.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.conf import settings


class CustomUser(AbstractUser):
    """
    Extends AbstractUser to include role-based permissions and subscriptions.

    Roles:
        reader:   Can read articles and follow publishers/journalists.
        journalist:  Can author articles and newsletters.
        editor:   Can review and approve or deny content.

    Attributes:
        role (str): The user’s role, chosen from ROLE_CHOICES.
        subscriptions_publishers (ManyToMany): Publishers this user follows.
        subscriptions_journalists (ManyToMany): Journalists this user follows.
    """

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

    subscriptions_publishers = models.ManyToManyField(
        'Publisher',
        blank=True,
        related_name='subscribers',
        help_text='Publishers you follow'
    )

    subscriptions_journalists = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='subscriber_set',
        help_text='Journalists you follow'
    )

    def is_reader(self):
        """Return True if the user’s role is ‘reader’."""
        return self.role == self.ROLE_READER

    def is_journalist(self):
        """Return True if the user’s role is ‘journalist’."""
        return self.role == self.ROLE_JOURNALIST

    def is_editor(self):
        """Return True if the user’s role is ‘editor’."""
        return self.role == self.ROLE_EDITOR

    def __str__(self):
        """
        Return the username and role for readability in Django admin and shell.
        """
        return f"{self.username} ({self.get_role_display()})"


class Publisher(models.Model):
    """
    Represents a media publisher, with associated editors and journalists.

    Attributes:
        name (str): Name of the publisher.
        description (str): Optional description.
        editors (ManyToMany): Users with editor role.
        journalists (ManyToMany): Users with journalist role.
    """

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
        """Return the publisher’s name."""
        return self.name


class Article(models.Model):
    """
    A news article submitted by a journalist and optionally reviewed by an editor.

    Attributes:
        title (str): Headline of the article.
        body (TextField): Main content.
        created_at (datetime): Timestamp when created.
        status (str): Review status, one of STATUS_CHOICES.
        publisher (ForeignKey): Publisher under which the article appears.
        author (ForeignKey): Journalist who wrote the article.
    """

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
        """Return the article’s title for display purposes."""
        return self.title

    def is_approved(self):
        """Return True if the article’s status is approved."""
        return self.status == self.STATUS_APPROVED

    def get_absolute_url(self):
        """
        Build and return the URL to view this article’s detail page.
        """
        return reverse('news:article-detail', args=[self.pk])


class Newsletter(models.Model):
    """
    A periodic newsletter authored by a journalist, optionally linked to a publisher.

    Attributes:
        title (str): Newsletter title.
        body (TextField): Newsletter content.
        author (ForeignKey): Journalist authoring the newsletter.
        publisher (ForeignKey, optional): Associated publisher.
        status (str): Review status, one of STATUS_CHOICES.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
    """

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
        """Return the newsletter’s title."""
        return self.title

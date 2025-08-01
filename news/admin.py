from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Publisher, Article, Newsletter


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': (
                'role',
                'subscriptions_publishers',
                'subscriptions_journalists',
            )
        }),
    )
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    filter_horizontal = ['editors', 'journalists']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    # Show status instead of the old approved boolean
    list_display = ['title', 'author', 'publisher', 'status', 'created_at']
    list_filter = ['status', 'publisher']
    search_fields = ['title', 'body', 'author__username']


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "publisher", "status", "created_at")
    list_filter = ("status", "publisher", "author")
    search_fields = ("title", "body")



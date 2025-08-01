# news/apps.py

from django.apps import AppConfig


class NewsConfig(AppConfig):
    name = 'news'

    def ready(self):
        import news.signals  # noqa: F401

        from django.db.models.signals import post_migrate
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from .models import Article, Newsletter

        def create_groups(sender, app_config, **kwargs):
            if app_config.name != self.name:
                return

            group_perms = {
                'reader': [
                    'view_article',
                    'view_newsletter',
                ],
                'journalist': [
                    'add_article',    'change_article',
                    'delete_article', 'view_article',
                    'add_newsletter', 'change_newsletter',
                    'delete_newsletter', 'view_newsletter',
                ],
                'editor': [
                    'change_article', 'delete_article',
                    'view_article',
                    'change_newsletter', 'delete_newsletter',
                    'view_newsletter',
                ],
            }

            art_ct = ContentType.objects.get_for_model(Article)
            nl_ct = ContentType.objects.get_for_model(Newsletter)

            for group_name, codenames in group_perms.items():
                group, _ = Group.objects.get_or_create(name=group_name)
                for codename in codenames:
                    # choose correct content type
                    ct = art_ct if 'article' in codename else nl_ct
                    perm = Permission.objects.filter(
                        content_type=ct, codename=codename
                    ).first()
                    if perm and perm not in group.permissions.all():
                        group.permissions.add(perm)

        post_migrate.connect(create_groups)

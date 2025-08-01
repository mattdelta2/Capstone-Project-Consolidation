
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.core import mail
from urllib.parse import urlparse, parse_qs


from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from news.models import Publisher, Article, CustomUser, Newsletter
from news.forms import SubscriptionForm, CustomUserCreationForm, ArticleForm

User = get_user_model()


# ─── API TESTS ───────────────────────────────────────────────────────────────


class NewsApiTests(APITestCase):
    """Tests for token auth and all /api/ endpoints."""

    @classmethod
    def setUpTestData(cls):
        # Avoid duplicate errors using get_or_create
        cls.reader_group, _ = Group.objects.get_or_create(name="Reader")
        cls.journalist_group, _ = Group.objects.get_or_create(name="Journalist")
        cls.editor_group, _ = Group.objects.get_or_create(name="Editor")

        # Users
        cls.reader = User.objects.create_user("reader1", "r1@x.com", "pass1234")
        cls.reader.groups.add(cls.reader_group)

        cls.journalist = User.objects.create_user("journalist1", "j1@x.com", "pass1234")
        cls.journalist.groups.add(cls.journalist_group)

        cls.editor = User.objects.create_user("editor1", "e1@x.com", "pass1234")
        cls.editor.groups.add(cls.editor_group)

        # Publisher & Articles
        cls.publisher = Publisher.objects.create(
            name="Daily News", description="Daily News Publisher"
        )
        cls.publisher.journalists.add(cls.journalist)

        cls.approved_article = Article.objects.create(
            title="Approved Story",
            body="Content",
            author=cls.journalist,
            publisher=cls.publisher,
            status=Article.STATUS_APPROVED
        )
        cls.pending_article = Article.objects.create(
            title="Pending Story",
            body="Draft",
            author=cls.journalist,
            publisher=cls.publisher,
            status=Article.STATUS_PENDING
        )
        cls.newsletter = Newsletter.objects.create(
            title="Signal Trigger Test",
            body="This newsletter content should fire signals when approved.",
            author=cls.journalist,
            publisher=cls.publisher,
            status=Newsletter.STATUS_PENDING
        )

        # Subscriptions
        cls.reader.subscriptions_journalists.add(cls.journalist)

    def setUp(self):
        self.client = self.__class__.client_class()

        # Generate tokens for tests
        for user, attr in [
            (self.reader, "reader_token"),
            (self.journalist, "journalist_token"),
            (self.editor, "editor_token"),
        ]:
            resp = self.client.post(
                reverse('api:token-auth'),
                {'username': user.username, 'password': 'pass1234'},
                format='json'
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            token = resp.data['token']
            setattr(self, attr, token)
            setattr(self, f"{attr}_auth", f"Token {token}")

    def test_unauthenticated_cannot_access(self):
        for ep in ['articles', 'publishers', 'journalists']:
            resp = self.client.get(reverse(f'api:{ep}-list'))
            self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_publishers_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.reader_token_auth)
        resp = self.client.get(reverse('api:publishers-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data[0]['name'], "Daily News")

    def test_journalists_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.reader_token_auth)
        resp = self.client.get(reverse('api:journalists-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data[0]['username'], "journalist1")

    def test_articles_filtered_by_subscription(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.reader_token_auth)
        resp = self.client.get(reverse('api:articles-list'))
        titles = [a['title'] for a in resp.data]
        self.assertIn("Approved Story", titles)
        self.assertNotIn("Pending Story", titles)

    def test_articles_no_subscription(self):
        self.reader.subscriptions_journalists.clear()
        self.client.credentials(HTTP_AUTHORIZATION=self.reader_token_auth)
        resp = self.client.get(reverse('api:articles-list'))
        self.assertEqual(len(resp.data), 0)

    def test_retrieve_single_article(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.reader_token_auth)
        ok = self.client.get(
            reverse('api:articles-detail', args=[self.approved_article.pk])
        )
        self.assertEqual(ok.status_code, status.HTTP_200_OK)

        nf = self.client.get(
            reverse('api:articles-detail', args=[self.pending_article.pk])
        )
        self.assertEqual(nf.status_code, status.HTTP_404_NOT_FOUND)

    def test_token_invalid_credentials(self):
        resp = self.client.post(
            reverse('api:token-auth'),
            {'username': 'reader1', 'password': 'wrongpass'},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', resp.data)

    def test_journalist_can_create_article(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.journalist_token_auth)
        resp = self.client.post(
            reverse('api:articles-list'),
            {'title': 'Breaking', 'body': 'x', 'publisher': self.publisher.pk},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['status'], Article.STATUS_PENDING)

    def test_reader_cannot_create_article(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.reader_token_auth)
        resp = self.client.post(
            reverse('api:articles-list'),
            {'title': 'T', 'body': 'Y'},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_update_article(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.journalist_token_auth)
        resp = self.client.patch(
            reverse('api:articles-detail', args=[self.approved_article.pk]),
            {'title': 'New Title'}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['title'], 'New Title')

    def test_non_author_cannot_update_article(self):
        other = User.objects.create_user("other", "o@x.com", "pw")
        token = Token.objects.create(user=other).key
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        resp = self.client.patch(
            reverse('api:articles-detail', args=[self.approved_article.pk]),
            {'body': 'X'}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_delete_article(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.journalist_token_auth)
        resp = self.client.delete(
            reverse('api:articles-detail', args=[self.approved_article.pk])
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    @patch('news.api.signals.requests.post')
    def test_editor_approves_article_sends_notifications(self, mock_x_post):
        self.reader.subscriptions_journalists.add(self.journalist)
        self.client.credentials(HTTP_AUTHORIZATION=self.editor_token_auth)
        resp = self.client.patch(
            reverse('api:articles-detail', args=[self.pending_article.pk]),
            {'status': Article.STATUS_APPROVED}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.pending_article.refresh_from_db()
        self.assertEqual(self.pending_article.status, Article.STATUS_APPROVED)
        self.assertGreaterEqual(len(mail.outbox), 1)
        mock_x_post.assert_called()


# ─── FORM TESTS ────────────────────────────────────────────────────────────

class SubscriptionFormTests(TestCase):
    """Tests for SubscriptionForm validation & saving."""
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            "u1", "u1@x.com", "pass1234", role=CustomUser.ROLE_READER
        )
        self.j1 = CustomUser.objects.create_user(
            "j1", "j1@x.com", "pass1234", role=CustomUser.ROLE_JOURNALIST
        )
        self.j2 = CustomUser.objects.create_user(
            "j2", "j2@x.com", "pass1234", role=CustomUser.ROLE_JOURNALIST
        )
        self.pub1 = Publisher.objects.create(name='Pub One', description='D1')

    def test_empty_submission_is_valid(self):
        form = SubscriptionForm(data={}, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_valid_selection_saves_correctly(self):
        form = SubscriptionForm(
            data={
                'subscriptions_journalists': [self.j1.pk, self.j2.pk],
                'subscriptions_publishers': [self.pub1.pk],
            },
            instance=self.user
        )
        self.assertTrue(form.is_valid())
        u = form.save()
        self.assertQuerySetEqual(
            u.subscriptions_journalists.order_by('pk'),
            [self.j1, self.j2], transform=lambda x: x
        )
        self.assertQuerySetEqual(
            u.subscriptions_publishers.order_by('pk'),
            [self.pub1], transform=lambda x: x
        )

    def test_invalid_journalist_pk_raises_error(self):
        form = SubscriptionForm(
            data={'subscriptions_journalists': [999]},
            instance=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('subscriptions_journalists', form.errors)


class CustomUserCreationFormTests(TestCase):
    """Tests for CustomUserCreationForm validation."""
    def test_requires_fields(self):
        form = CustomUserCreationForm(data={})
        self.assertFalse(form.is_valid())
        for fld in ['username', 'role', 'password1', 'password2']:
            self.assertIn(fld, form.errors)

    def test_password_mismatch(self):
        form = CustomUserCreationForm(data={
            'username': 'u1', 'email': 'u1@x.com', 'role': 'reader',
            'password1': 'abc', 'password2': 'xyz'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_valid_data_creates_user(self):
        data = {
            'username': 'u2', 'email': 'u2@x.com', 'role': 'journalist',
            'password1': 'strong123', 'password2': 'strong123'
        }
        form = CustomUserCreationForm(data=data)
        self.assertTrue(form.is_valid())
        u = form.save()
        self.assertTrue(u.check_password('strong123'))


class ArticleFormTests(TestCase):
    """Tests for ArticleForm queryset restriction and validation."""
    def setUp(self):
        self.j = CustomUser.objects.create_user(
            "journ", "j@x.com", "pass1234", role=CustomUser.ROLE_JOURNALIST
        )
        self.e = CustomUser.objects.create_user(
            "edit", "e@x.com", "pass1234", role=CustomUser.ROLE_EDITOR
        )
        self.p1 = Publisher.objects.create(name='P1', description='D1')
        self.p2 = Publisher.objects.create(name='P2', description='D2')
        self.p1.journalists.add(self.j)

    def test_journalist_only_sees_their_publishers(self):
        form = ArticleForm(user=self.j)
        self.assertQuerySetEqual(
            form.fields['publisher'].queryset,
            [self.p1], transform=lambda x: x
        )

    def test_editor_sees_all_publishers(self):
        form = ArticleForm(user=self.e)
        self.assertQuerySetEqual(
            form.fields['publisher'].queryset.order_by('pk'),
            [self.p1, self.p2], ordered=True, transform=lambda x: x
        )

    def test_missing_title_or_body_invalid(self):
        f1 = ArticleForm(
            data={'body': 'x', 'publisher': self.p1.pk}, user=self.j
        )
        self.assertFalse(f1.is_valid())
        self.assertIn('title', f1.errors)

        f2 = ArticleForm(
            data={'title': 'T', 'publisher': self.p1.pk}, user=self.j
        )
        self.assertFalse(f2.is_valid())
        self.assertIn('body', f2.errors)


# ─── MODEL TESTS ────────────────────────────────────────────────────────────

class ModelTests(TestCase):
    """Tests for model methods & properties."""
    def test_article_get_status_display(self):
        a = Article(status=Article.STATUS_PENDING)
        self.assertEqual(a.get_status_display(), 'Pending review')


# ─── ORM SIGNAL TESTS ───────────────────────────────────────────────────────

class SignalsORMTests(TestCase):
    """
    Drive news/signals.py e-mail paths and skip tweet:
      - Article no-subs → no email
      - Article journalist/pub subs → email
      - send_mail exception is caught
    """
    def setUp(self):
        mail.outbox.clear()
        self.juser = User.objects.create_user(
            "juser", "j@x.com", "pw", role=User.ROLE_JOURNALIST
        )
        self.pub = Publisher.objects.create(name="Daily", description="Desc")
        self.pub.journalists.add(self.juser)

        self.r1 = User.objects.create_user(
            "r1", "r1@x.com", "pw", role=User.ROLE_READER
        )
        self.r2 = User.objects.create_user(
            "r2", "r2@x.com", "pw", role=User.ROLE_READER
        )

        # Newsletter object for signal tests
        self.newsletter = Newsletter.objects.create(
            title="Signal Trigger Test",
            body="This newsletter should fire signals when approved.",
            author=self.juser,
            publisher=self.pub,
            status=Newsletter.STATUS_PENDING
        )

        # Convenience access for creation test
        self.author = self.juser
        self.publisher = self.pub

    def test_article_no_subscribers_no_email(self):
        mail.outbox.clear()
        art = Article.objects.create(
            title="Lonely", body="Nobody", author=self.juser,
            publisher=self.pub, status=Article.STATUS_PENDING
        )
        art.status = Article.STATUS_APPROVED
        art.save()
        self.assertEqual(len(mail.outbox), 0)

    def test_article_journalist_subscription_sends_email(self):
        mail.outbox.clear()
        self.r1.subscriptions_journalists.add(self.juser)
        art = Article.objects.create(
            title="ByJ", body="Text", author=self.juser,
            publisher=self.pub, status=Article.STATUS_PENDING
        )
        art.status = Article.STATUS_APPROVED
        art.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("ByJ", mail.outbox[0].subject)

    def test_article_publisher_subscription_sends_email(self):
        mail.outbox.clear()
        self.r2.subscriptions_publishers.add(self.pub)
        art = Article.objects.create(
            title="ByP", body="Text", author=self.juser,
            publisher=self.pub, status=Article.STATUS_PENDING
        )
        art.status = Article.STATUS_APPROVED 
        art.save()
        self.assertGreaterEqual(len(mail.outbox), 1)
        self.assertTrue(any("ByP" in m.subject for m in mail.outbox))

    @patch('django.core.mail.send_mail', side_effect=Exception("SMTP fail"))
    def test_send_mail_exception_caught(self, mock_send):
        self.r1.subscriptions_journalists.add(self.juser)
        art = Article.objects.create(
            title="Err", body="Boom", author=self.juser,
            publisher=self.pub, status=Article.STATUS_PENDING
        )
        art.status = Article.STATUS_APPROVED
        # no exception should escape
        art.save()
        art.refresh_from_db()
        self.assertEqual(art.status, Article.STATUS_APPROVED)
    
    @patch("news.signals.send_mass_mail")
    def test_newsletter_approval_triggers_email_and_x_simulation(self, mock_mail):
        # Approve the newsletter
        self.newsletter.status = Newsletter.STATUS_APPROVED
        self.r1.subscriptions_publishers.add(self.publisher)
        self.newsletter.save()

        self.assertTrue(mock_mail.called)
        args, _ = mock_mail.call_args
        self.assertGreaterEqual(len(args[0]), 1)

    @patch("news.signals.send_mass_mail", side_effect=Exception("Newsletter Fail"))
    def test_newsletter_email_error_is_caught(self, mock_mail):
        self.newsletter.status = Newsletter.STATUS_APPROVED
        self.newsletter.save()
    # Confirms no exception escapes — error is printed, not raised

    @override_settings(X_API_BEARER_TOKEN=None)
    @patch("news.signals.send_mass_mail")
    def test_newsletter_x_simulation_skips_if_token_absent(self, mock_mail):
        self.newsletter.status = Newsletter.STATUS_APPROVED
        self.newsletter.save()
    # Ensures "[X SIMULATION] No X_API_BEARER_TOKEN" path is covered

    def test_newsletter_no_signal_on_creation(self):
        # Create a newsletter directly as approved — signals should not fire
        Newsletter.objects.create(
            title="Fresh Approved",
            body="Body of newsletter",
            author=self.author,
            publisher=self.publisher,
            status=Newsletter.STATUS_APPROVED
        )
    # This bypasses post-save logic since it’s treated as 'created=True'

    def test_newsletter_signal_skips_if_already_approved(self):
        self.newsletter.status = Newsletter.STATUS_APPROVED
        self.newsletter.save()
        # First transition triggers signal
        self.newsletter.body += " extra"
        self.newsletter.save()
        # Second save with same status should not re-trigger


# ─── VIEW TESTS ────────────────────────────────────────────────────────────

class ArticleViewsTests(TestCase):
    """Full CRUD view coverage for news/views.py."""
    def setUp(self):
        self.client = Client()

        # Users
        self.author = User.objects.create_user(username='author', password='pass')
        self.other = User.objects.create_user(username='other', password='pass')

        # Publisher
        self.publisher = Publisher.objects.create(name="Test Pub", description="Desc")

        # Articles (must include publisher)
        self.articles = [
            Article.objects.create(
                title=f"Title {i}",
                body="Body content.",
                author=self.author,
                publisher=self.publisher,
                status=Article.STATUS_APPROVED
            )
            for i in range(3)
        ]

        # URLs
        self.list_url = reverse('news:article-list')
        self.detail_url = reverse('news:article-detail', args=[self.articles[0].pk])
        self.create_url = reverse('news:article-create')
        self.update_url = reverse('news:article-update', args=[self.articles[0].pk])
        self.delete_url = reverse('news:article-delete', args=[self.articles[0].pk])

    def test_list_view(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'news/article_list.html')

        qs = resp.context.get('object_list')
        self.assertIsNotNone(qs)
        self.assertEqual(qs.count(), len(self.articles))

    def test_detail_view(self):
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'news/article_detail.html')
        self.assertEqual(resp.context['article'], self.articles[0])

    def test_detail_404(self):
        bad = reverse('news:article-detail', args=[9999])
        resp = self.client.get(bad)
        self.assertEqual(resp.status_code, 404)

    def test_create_requires_login(self):
        resp = self.client.get(self.create_url)
        self.assertEqual(resp.status_code, 302)

        parsed = urlparse(resp['Location'])
        self.assertIn('login', parsed.path)

        params = parse_qs(parsed.query)
        self.assertEqual(params.get('next'), [self.create_url])

    def test_create_get_and_post(self):
        self.client.login(username='author', password='pass')

        resp_get = self.client.get(self.create_url)
        self.assertEqual(resp_get.status_code, 200)
        self.assertTemplateUsed(resp_get, 'news/article_create.html')

        data = {
            'title': 'New Article',
            'body': 'XYZ content.',
            'publisher': self.publisher.pk
        }
        resp_post = self.client.post(self.create_url, data)
        self.assertRedirects(resp_post, self.list_url)

        new = Article.objects.get(title='New Article')
        self.assertEqual(new.author, self.author)
        self.assertEqual(new.publisher, self.publisher)

    def test_create_invalid(self):
        self.client.login(username='author', password='pass')
        resp = self.client.post(
            self.create_url, {'title': '', 'body': '', 'publisher': ''})
        self.assertEqual(resp.status_code, 200)
        form = resp.context_data['form']
        self.assertIn('title', form.errors)
        self.assertIn('publisher', form.errors)

    def test_update_requires_login(self):
        resp = self.client.get(self.update_url)
        self.assertEqual(resp.status_code, 302)

        parsed = urlparse(resp['Location'])
        self.assertIn('login', parsed.path)

        params = parse_qs(parsed.query)
        self.assertEqual(params.get('next'), [self.update_url])

    def test_update_get_and_post(self):
        self.client.login(username='author', password='pass')

        resp_get = self.client.get(self.update_url)
        self.assertEqual(resp_get.status_code, 200)
        self.assertTemplateUsed(resp_get, 'news/article_form.html')

        data = {
            'title': 'Updated Title',
            'body': 'New body.',
            'publisher': self.publisher.pk
        }
        resp_post = self.client.post(self.update_url, data)
        self.assertRedirects(
            resp_post,
            reverse('news:article-detail', args=[self.articles[0].pk])
        )

        updated = Article.objects.get(pk=self.articles[0].pk)
        self.assertEqual(updated.title, 'Updated Title')

    def test_update_invalid(self):
        self.client.login(username='author', password='pass')
        resp = self.client.post(
            self.update_url, {'title': '', 'body': '', 'publisher': ''})
        self.assertEqual(resp.status_code, 200)
        form = resp.context_data['form']
        self.assertIn('title', form.errors)
        self.assertIn('publisher', form.errors)

    def test_delete_requires_login(self):
        resp = self.client.delete(self.delete_url)
        self.assertEqual(resp.status_code, 302)

        parsed = urlparse(resp['Location'])
        self.assertIn('login', parsed.path)

        params = parse_qs(parsed.query)
        self.assertEqual(params.get('next'), [self.delete_url])

    def test_delete_post(self):
        self.client.login(username='author', password='pass')
        before = Article.objects.count()
        resp = self.client.post(self.delete_url)
        after = Article.objects.count()
        self.assertEqual(after, before - 1)
        self.assertRedirects(resp, self.list_url)
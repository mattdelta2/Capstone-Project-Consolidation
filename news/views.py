# news/views.py

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
    )
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Article, CustomUser, Newsletter, Publisher
from .forms import SubscriptionForm, CustomUserCreationForm
from django.db.models import Q


# -----------------------------------------------------------------------------
# 1) Role helpers
# -----------------------------------------------------------------------------
def is_reader(user):
    return user.is_authenticated and user.role == CustomUser.ROLE_READER


def is_journalist(user):
    return user.is_authenticated and user.role == CustomUser.ROLE_JOURNALIST


def is_editor(user):
    return user.is_authenticated and user.role == CustomUser.ROLE_EDITOR


# -----------------------------------------------------------------------------
# 2) Approve / Deny only pending articles
# -----------------------------------------------------------------------------
@login_required
@user_passes_test(is_editor)
def approve_article(request, pk):
    article = get_object_or_404(Article, pk=pk, status=Article.STATUS_PENDING)
    article.status = Article.STATUS_APPROVED
    article.save()
    messages.success(request, "Article approved.")
    return redirect("news:article-list")


@login_required
@user_passes_test(is_editor)
def deny_article(request, pk):
    article = get_object_or_404(Article, pk=pk, status=Article.STATUS_PENDING)
    article.status = Article.STATUS_DENIED
    article.save()
    messages.warning(request, "Article denied.")
    return redirect("news:article-list")


# -----------------------------------------------------------------------------
# 3) Public homepage: only approved articles & newsletters
# -----------------------------------------------------------------------------
class ArticleListView(ListView):
    model = Article
    template_name = "news/article_list.html"
    context_object_name = "articles"
    paginate_by = 10

    def get_queryset(self):
        qs = Article.objects.filter(status=Article.STATUS_APPROVED)
        view = self.request.GET.get("view")
        if view == "subscribed" and is_reader(self.request.user):
            user = self.request.user
            j_ids = user.subscriptions_journalists.values_list("pk", flat=True)
            p_ids = user.subscriptions_publishers.values_list("pk", flat=True)
            qs = qs.filter(Q(author_id__in=j_ids) | Q(publisher_id__in=p_ids))
        return qs.order_by("-created_at")


class NewsletterListView(ListView):
    model = Newsletter
    template_name = "news/newsletter_list.html"
    context_object_name = "newsletters"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        view = self.request.GET.get("view")
        if is_editor(user):
            qs = Newsletter.objects.all()
        else:
            qs = Newsletter.objects.filter(status=Newsletter.STATUS_APPROVED)
            if view == "subscribed" and is_reader(user):
                j_ids = user.subscriptions_journalists.values_list("pk", flat=True)
                p_ids = user.subscriptions_publishers.values_list("pk", flat=True)
                qs = qs.filter(Q(author_id__in=j_ids) | Q(publisher_id__in=p_ids))
        return qs.order_by("-created_at")


# -----------------------------------------------------------------------------
# 4) Newsletter detail
# -----------------------------------------------------------------------------
class NewsletterDetailView(DetailView):
    model = Newsletter
    template_name = "news/newsletter_detail.html"

    def get_queryset(self):
        if is_editor(self.request.user):
            return Newsletter.objects.all()
        return Newsletter.objects.filter(status=Newsletter.STATUS_APPROVED)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        nl = self.object

        # Editors get review buttons & status
        ctx["can_review"] = is_editor(user)

        # Readers get subscribe/unsubscribe flags
        if user.is_authenticated and not is_editor(user):
            ctx["subscribed_to_author"] = (
                user.subscriptions_journalists.filter(pk=nl.author.pk).exists()
            )
            ctx["subscribed_to_publisher"] = (
                user.subscriptions_publishers.filter(pk=nl.publisher.pk).exists()
            )
        return ctx


# -----------------------------------------------------------------------------
# 5) Article detail
# -----------------------------------------------------------------------------
class ArticleDetailView(DetailView):
    model = Article
    template_name = "news/article_detail.html"

    def get_queryset(self):
        if is_editor(self.request.user):
            return Article.objects.all()
        return Article.objects.filter(status=Article.STATUS_APPROVED)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        article = self.object

        # Editors get review buttons & status
        ctx["can_review"] = is_editor(user)

        # Readers get follow/unfollow flags
        if user.is_authenticated and not is_editor(user):
            ctx["subscribed_to_author"] = (
                user.subscriptions_journalists.filter(pk=article.author.pk).exists()
            )
            ctx["subscribed_to_publisher"] = (
                user.subscriptions_publishers.filter(pk=article.publisher.pk).exists()
            )
        return ctx


# -----------------------------------------------------------------------------
# 6) Editor dashboard: pending newsletters
# -----------------------------------------------------------------------------
class PendingNewslettersListView(LoginRequiredMixin, ListView):
    model = Newsletter
    template_name = "news/pending_newsletters.html"
    context_object_name = "pending_newsletters"

    def get_queryset(self):
        return Newsletter.objects.filter(
            status=Newsletter.STATUS_PENDING).order_by("-created_at")


# -----------------------------------------------------------------------------
# 7) Subscribe / Unsubscribe Views
# -----------------------------------------------------------------------------
@login_required
def subscribe_journalist(request, pk):
    journalist = get_object_or_404(CustomUser, pk=pk, role=CustomUser.ROLE_JOURNALIST)
    request.user.subscriptions_journalists.add(journalist)
    messages.success(request, f"Now subscribed to {journalist.username}.")
    return redirect(request.GET.get("next", "news:article-list"))


@login_required
def unsubscribe_journalist(request, pk):
    journalist = get_object_or_404(CustomUser, pk=pk, role=CustomUser.ROLE_JOURNALIST)
    request.user.subscriptions_journalists.remove(journalist)
    messages.info(request, f"You have unsubscribed from {journalist.username}.")
    return redirect(request.GET.get("next", "news:article-list"))


@login_required
def subscribe_publisher(request, pk):
    publisher = get_object_or_404(Publisher, pk=pk)
    request.user.subscriptions_publishers.add(publisher)
    messages.success(request, f"Now subscribed to {publisher.name}.")
    return redirect(request.GET.get("next", "news:article-list"))


@login_required
def unsubscribe_publisher(request, pk):
    publisher = get_object_or_404(Publisher, pk=pk)
    request.user.subscriptions_publishers.remove(publisher)
    messages.info(request, f"You have unsubscribed from {publisher.name}.")
    return redirect(request.GET.get("next", "news:article-list"))


# -----------------------------------------------------------------------------
# 8) Manage subscriptions via a form
# -----------------------------------------------------------------------------
class SubscriptionUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = SubscriptionForm
    template_name = "news/subscriptions.html"
    success_url = reverse_lazy("news:subscriptions")

    def get_object(self):
        return self.request.user

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        user = self.request.user
        form.fields["subscriptions_journalists"].initial = user. \
            subscriptions_journalists.all()
        form.fields["subscriptions_publishers"].initial = user. \
            subscriptions_publishers.all()
        return form

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        self.object.subscriptions_journalists.set(
            form.cleaned_data["subscriptions_journalists"])
        self.object.subscriptions_publishers.set(
            form.cleaned_data["subscriptions_publishers"])
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        j_ids = user.subscriptions_journalists.values_list("pk", flat=True)
        p_ids = user.subscriptions_publishers.values_list("pk", flat=True)
        ctx["articles"] = (
            Article.objects
            .filter(Q(author_id__in=j_ids) | Q(publisher_id__in=p_ids), 
                    status=Article.STATUS_APPROVED)
            .select_related("author", "publisher")
            .order_by("-created_at")
        )
        return ctx


# -----------------------------------------------------------------------------
# 9) Sign up
# -----------------------------------------------------------------------------
class SignupView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")


# -----------------------------------------------------------------------------
# 10) Editor dashboard: pending articles
# -----------------------------------------------------------------------------
class PendingArticlesListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = "news/pending_articles.html"
    context_object_name = "pending_articles"

    def get_queryset(self):
        return Article.objects.filter(
            status=Article.STATUS_PENDING).order_by("-created_at")


# -----------------------------------------------------------------------------
# 11) Journalists create articles & newsletters
# -----------------------------------------------------------------------------
class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    fields = ["title", "body", "publisher"]
    template_name = "news/article_create.html"
    success_url = reverse_lazy("news:article-list")
    login_url = reverse_lazy("login")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class NewsletterCreateView(LoginRequiredMixin, CreateView):
    model = Newsletter
    fields = ["title", "body", "publisher"]
    template_name = "news/newsletter_form.html"
    success_url = reverse_lazy("news:newsletter-list")

    def dispatch(self, request, *args, **kwargs):
        if not is_journalist(request.user):
            return redirect("news:article-list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


# -----------------------------------------------------------------------------
# 12) Approve / Deny newsletters (editors only)
# -----------------------------------------------------------------------------
@login_required
@user_passes_test(is_editor)
def approve_newsletter(request, pk):
    nl = get_object_or_404(Newsletter, pk=pk, status=Newsletter.STATUS_PENDING)
    nl.status = Newsletter.STATUS_APPROVED
    nl.save()
    messages.success(request, "Newsletter approved.")
    return redirect("news:newsletter-list")


@login_required
@user_passes_test(is_editor)
def deny_newsletter(request, pk):
    nl = get_object_or_404(Newsletter, pk=pk, status=Newsletter.STATUS_PENDING)
    nl.status = Newsletter.STATUS_DENIED
    nl.save()
    messages.warning(request, "Newsletter denied.")
    return redirect("news:newsletter-list")


class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    fields = ['title', 'body', 'publisher']
    template_name = 'news/article_form.html'

    def test_func(self):
        return self.get_object().author == self.request.user


class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    template_name = 'news/article_confirm_delete.html'
    success_url = reverse_lazy('news:article-list')

    def test_func(self):
        return self.get_object().author == self.request.user
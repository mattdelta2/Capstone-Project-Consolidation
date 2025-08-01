# news/forms.py
from django import forms
from .models import CustomUser, Article, Publisher
from django.contrib.auth.forms import UserCreationForm


class SubscriptionForm(forms.ModelForm):
    subscriptions_journalists = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role=CustomUser.ROLE_JOURNALIST),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Follow Journalists"
    )
    subscriptions_publishers = forms.ModelMultipleChoiceField(
        queryset=Publisher.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Follow Publishers"
    )

    class Meta:
        model = CustomUser
        fields = [
            "subscriptions_journalists",
            "subscriptions_publishers",
        ]


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'body', 'publisher']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')                # pop the request user
        super().__init__(*args, **kwargs)

        # Restrict publishers to those the journalist belongs to
        if user.role == 'journalist':
            self.fields['publisher'].queryset = (
                user.publisher_journalist_set.all()
            )
        else:
            # Editors/readers can see all or adjust as needed
            self.fields['publisher'].queryset = Publisher.objects.all()
            
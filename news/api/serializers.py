# news/api/serializers.py

from django.contrib.auth import get_user_model
from rest_framework import serializers
from news.models import Article, Publisher

User = get_user_model()


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description']


class JournalistSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class ArticleSerializer(serializers.ModelSerializer):
    author = JournalistSerializer(read_only=True)

    # allow clients to supply a publisher ID on create/update
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all()
    )

    # expose status as a ChoiceField so editors can flip it
    status = serializers.ChoiceField(
        choices=Article.STATUS_CHOICES,
        default=Article.STATUS_PENDING
    )

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'body',
            'created_at',
            'status',
            'author',
            'publisher',
        ]
        read_only_fields = (
            'id',
            'author',      # set automatically in view
            'created_at',
        )

    def validate_status(self, value):
        """
        Only allow status changes if the user is staff or in the Editor group.
        """
        # if this is an update (instance exists) and they’re actually changing it…
        if self.instance and value != self.instance.status:
            user = self.context['request'].user
            is_editor = user.groups.filter(name="Editor").exists()
            if not (user.is_staff or is_editor):
                raise serializers.ValidationError(
                    "Only editors or staff may change an article’s status."
                )
        return value

    def to_representation(self, instance):
        """
        Return nested publisher details on GET responses.
        """
        ret = super().to_representation(instance)
        ret['publisher'] = PublisherSerializer(instance.publisher).data
        return ret

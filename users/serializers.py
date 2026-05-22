from rest_framework import serializers
from users.models import User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    posts = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="post-detail",  # Sesuaikan dengan name di urls.py Anda
        lookup_field="slug",  # Menggunakan slug sebagai parameter URL
    )
    initial_name = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "url",
            "first_name",
            "last_name",
            "initial_name",
            "username",
            "email",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "total_views",
            "total_comments",
            "posts",
        ]
        extra_kwargs = {
            "url": {"view_name": "user-detail", "lookup_field": "username"},
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def get_initial_name(self, obj):
        return obj.get_initial_name()

    def get_total_views(self, obj):
        posts = obj.posts.all()
        count = 0
        for post in posts:
            count += post.views
        return count

    def get_total_comments(self, obj):
        posts = obj.posts.all()
        count = 0
        for post in posts:
            count += post.comments.all().count()
        return count


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "is_superuser",
            "is_staff",
            "is_active",
            "date_joined",
        ]

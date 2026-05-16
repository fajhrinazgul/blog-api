from rest_framework import serializers
from blogs.models import Category, Tag, Post, Comment, CommentReply
from django.utils.translation import gettext_lazy as _
# from django.contrib.auth import get_user_model

# User = get_user_model()

# from users.serializers import UserSerializer


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    # posts = serializers.HyperlinkedRelatedField(
    #     many=True, read_only=True, view_name="post-detail", lookup_field="slug"
    # )

    class Meta:
        model = Category
        fields = ["url", "name", "slug"]
        extra_kwargs = {"url": {"read_only": True, "lookup_field": "slug"}}


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


# class UserMinifiedSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "username"]


class CommentReplySerializer(serializers.HyperlinkedModelSerializer):
    comment = serializers.SerializerMethodField()
    commenter = serializers.HyperlinkedRelatedField(
        view_name="user-detail", lookup_field="username", read_only=True
    )
    url = serializers.SerializerMethodField()

    class Meta:
        model = CommentReply
        fields = [
            "url",
            "comment",
            "commenter",
            "title",
            "content",
            "is_approved",
            "created_at",
            "updated_at",
        ]

    def get_url(self, obj):
        """Membangun URL untuk detail reply (3 parameter)"""
        request = self.context.get("request")
        if request is not None:
            from rest_framework.reverse import reverse

            return reverse(
                "post-comment-reply-detail",
                kwargs={
                    "slug": obj.comment.post.slug,
                    "comment_id": obj.comment.id,
                    "reply_id": obj.id,
                },
                request=request,
            )
        return None

    def get_comment(self, obj):
        """Membangun URL untuk detail komentar induknya"""
        request = self.context.get("request")
        if request is not None:
            from rest_framework.reverse import reverse

            return reverse(
                "post-comment-detail",
                kwargs={"slug": obj.comment.post.slug, "id": obj.comment.id},
                request=request,
            )
        return None


class CommentSerializer(serializers.HyperlinkedModelSerializer):
    commenter = serializers.HyperlinkedRelatedField(
        view_name="user-detail", lookup_field="username", read_only=True
    )
    post = serializers.HyperlinkedRelatedField(
        view_name="post-detail", read_only=True, lookup_field="slug"
    )
    # replies = CommentReplySerializer(many=True, read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "url",
            "post",
            "commenter",
            "title",
            "content",
            "is_approved",
            # "replies",
            "created_at",
            "updated_at",
        ]

    def get_url(self, obj):
        """
        Secara manual membangun URL dengan parameter slug dan id komentar
        agar cocok dengan konfigurasi path('posts/<str:slug>/comments/<int:id>/')
        """
        request = self.context.get("request")
        if request is not None:
            from rest_framework.reverse import reverse

            return reverse(
                "post-comment-detail",  # Pastikan nama name di urls.py sesuai
                kwargs={"slug": obj.post.slug, "id": obj.id},
                request=request,
            )
        return None


class PostSerializer(serializers.HyperlinkedModelSerializer):
    category = serializers.StringRelatedField(source="category.name")
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.CharField(max_length=50, write_only=True, required=False)
    category_slug = serializers.CharField(max_length=50, write_only=True, required=True)
    author = serializers.HyperlinkedRelatedField(
        view_name="user-detail", lookup_field="username", read_only=True
    )
    # comments = serializers.

    class Meta:
        model = Post
        fields = [
            "url",
            "category",
            "tag_names",
            "category_slug",
            "author",
            "title",
            "slug",
            "logo",
            "summary",
            "content",
            "views",
            "status",
            "reading_time",
            "updated_at",
            "created_at",
            "tags",
        ]
        extra_kwargs = {
            "url": {
                "view_name": "post-detail",
                "lookup_field": "slug",
                "read_only": True,
            }
        }

    def validate_category_slug(self, value):
        try:
            return Category.objects.get(slug=value)
        except Category.DoesNotExist:
            raise serializers.ValidationError(
                _(f"Category with '{value}' is not found")
            )

    def create(self, validated_data):
        tag_names = validated_data.pop("tag_names", None)
        category_slug = validated_data.pop("category_slug")
        category = self.validate_category_slug(category_slug)

        request = self.context.get("request")
        if request and hasattr(request, "user"):
            post = Post.objects.create(
                author=request.user,
                category=category,
                title=validated_data["title"],
                logo=validated_data["logo"],
                content=validated_data["content"],
            )

        if tag_names is not None:
            names = tag_names.split(",")
            for name in names:
                tag, created = Tag.objects.get_or_create(name=name.strip())
                post.tags.add(tag)
        return post

    def update(self, instance, validated_data):
        # 1. Ambil data tag_names menggunakan .pop() dengan default value None.
        # Jika nilainya None (tidak dikirim di JSON), kita tidak akan mengubah tags lama.
        tag_names = validated_data.pop("tag_names", None)
        category_slug = validated_data.pop("category_slug", None)
        status = validated_data.pop("status", None)

        # 2. Update field bawaan model Post (title, content, category, logo, dll)
        # super().update() secara otomatis menangani partial update untuk field standar.
        instance = super().update(instance, validated_data)

        # 3. Logika untuk update Tags jika 'tag_names' dikirim oleh frontend
        if tag_names is not None:
            tag_objects = []
            names = tag_names.split(",")
            for name in names:
                tag, created = Tag.objects.get_or_create(name=name.strip())
                tag_objects.append(tag)

            # .set() akan mengganti semua tag lama dengan daftar tag yang baru
            instance.tags.set(tag_objects)

        if category_slug is not None:
            category = self.validate_category_slug(category_slug)
            instance.category = category

        if status is not None:
            instance.status = status.upper()

        return instance

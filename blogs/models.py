import os
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils.text import slugify

from bs4 import BeautifulSoup
import markdown
import math
import re


AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "users.User")


class Category(models.Model):
    name = models.CharField(_("name"), max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


def get_post_image_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return os.path.join(
        "posts",
        instance.slug,
        str(uuid.uuid5(uuid.NAMESPACE_DNS, instance.slug)).replace("-", "") + ext,
    )


class Tag(models.Model):
    name = models.CharField(_("name"), max_length=20, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    PUBLISHED = "PUBLISHED"
    DRAFTED = "DRAFTED"

    STATUS_CHOICES = (
        (PUBLISHED, "published"),
        (DRAFTED, "drafted"),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    author = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_("author"),
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(_("title"), max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)
    logo = models.ImageField(upload_to=get_post_image_path)
    summary = models.CharField(max_length=255, blank=True, null=True, editable=False)
    content = models.TextField()
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    views = models.PositiveIntegerField(default=0)
    reading_time = models.CharField(
        _("reading time"), max_length=20, blank=True, editable=False
    )
    status = models.CharField(
        _("status"), max_length=9, choices=STATUS_CHOICES, default=DRAFTED
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # auto increment slug
        base_slug = slugify(self.title, allow_unicode=True)
        slug = base_slug
        counter = 1
        Klass = self.__class__
        while Klass.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug

        # auto summary
        if self.content:
            html_content = markdown.markdown(self.content)
            cleaned_text = BeautifulSoup(html_content, "html.parser").get_text()
            cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
            if len(cleaned_text) > 250:
                self.summary = f"{cleaned_text[:247]}..."
            else:
                self.summary = cleaned_text

        # auto reading time
        if self.content:
            word_count = len(cleaned_text.split())
            # 200 WPM
            words_per_minute = 200
            minutes = math.ceil(word_count / words_per_minute)
            self.reading_time = f"{minutes} min read"
        else:
            self.reading_time = "0 min read"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PostViewLog(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="view_logs")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Memastikan user yang sama tidak mencatat log ganda pada post yang sama
        # (Opsi ini efektif jika hanya ingin menghitung 1 view per user selamanya)
        unique_together = ("post", "user")


class BaseComment(models.Model):
    title = models.CharField(_("title"), max_length=100)
    content = models.TextField(_("content"))
    is_approved = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Comment(BaseComment):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    commenter = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")

    def __str__(self):
        return f"{self.commenter.username} comment on {self.post.slug}"


class CommentReply(BaseComment):
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="comments"
    )
    commenter = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Comment Reply")
        verbose_name_plural = _("Comment Replies")

    def __str__(self):
        return f"Reply ID: {self.pk}"

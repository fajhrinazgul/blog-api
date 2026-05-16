from django.contrib import admin

# Register your models here.
from blogs.models import Category, Tag, Post, Comment, CommentReply


class CategoryAdmin(admin.ModelAdmin):
    pass


class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        "slug": ("title",),
    }


admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Tag)
admin.site.register(CommentReply)
admin.site.register(Comment)

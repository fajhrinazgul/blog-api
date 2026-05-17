from django.urls import path

from blogs import views

urlpatterns = [
    path("api/posts/", views.PostListView.as_view(), name="post-list"),
    path("api/posts/<str:slug>/", views.PostDetailView.as_view(), name="post-detail"),
    path(
        "api/posts/<str:slug>/comments/",
        views.CommentListView.as_view(),
        name="post-comment-list",
    ),
    path(
        "api/posts/<str:slug>/comments/<int:id>/",
        views.CommentDetailView.as_view(),
        name="post-comment-detail",
    ),
    path(
        "api/posts/<str:slug>/comments/<int:comment_id>/replies/",
        views.CommentReplyListView.as_view(),
        name="post-comment-reply-list",
    ),
    path(
        "api/posts/<str:slug>/comments/<int:comment_id>/replies/<int:reply_id>/",
        views.CommentReplyDetailView.as_view(),
        name="post-comment-reply-detail",
    ),
    path("api/categories/", views.CategoryListView.as_view(), name="category-list"),
    path(
        "api/categories/<str:slug>/",
        views.CategoryDetailView.as_view(),
        name="category-detail",
    ),
]

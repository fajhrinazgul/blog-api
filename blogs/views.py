from django.shortcuts import render
from rest_framework import generics
from rest_framework.generics import Http404
from rest_framework.generics import get_object_or_404
from rest_framework import permissions
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from users.paginations import CustomLimitOffsetPagination
from blogs.models import Tag, Category, Post, PostViewLog, Comment, CommentReply
from blogs.permissions import (
    IsAdminOrReadOnly,
    IsAdminOrPostOwnerReadOnly,
    IsOwnerPostOrCommenterReadOnly,
    IsOwnerOrCommenter,
)
from blogs.serializers import (
    TagSerializer,
    PostSerializer,
    CategorySerializer,
    CommentSerializer,
    CommentReplySerializer,
)
from datetime import timedelta


class PostListView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    pagination_class = CustomLimitOffsetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        queryset = Post.objects.all()

        status_param = self.request.query_params.get("status", "PUBLISHED")
        author_param = self.request.query_params.get("author", None)
        search_param = self.request.query_params.get("search", None)

        # Filter berdasarkan author
        if author_param is not None:
            queryset = queryset.filter(author__username=author_param)

        # Filter berdasarkan status dengan pengecekan kondisi DRAFTED
        if status_param is not None:
            status_upper = status_param.upper()

            if status_upper == "DRAFTED":
                # Jika user belum login: OTomatis tidak boleh melihat data DRAFTED
                if not user.is_authenticated:
                    raise PermissionDenied(_("You must login to get DRAFTED data."))
                # jika user sudah login: Hanya filter draft milik user yang login
                queryset = queryset.filter(status="DRAFTED", author=user)
            else:
                queryset = queryset.filter(status=status_upper)
        else:
            # KONDISI JIKA URL TANPA PARAMETER STATUS (?status tidak diisi)
            # Standarnya, user anonim atau user lain tidak boleh melihat DRAFT orang lain di list utama.
            if user.is_authenticated:
                # Tampilkan semua yang PUBLISHED, ATAU yang berstatus DRAFT tetapi milik user itu sendiri
                queryset = queryset.filter(
                    Q(status="PUBLISHED") | Q(status="DRAFTED"), author=user
                )
            else:
                # Jika anonim, hanya boleh melihat yang PUBLISHED saja
                queryset = queryset.filter(status="PUBLISHED")

        # Filter search parameter
        if search_param is not None:
            # icontains = case-insensitive search (tidak peduli huruf besar/kecil)
            # Mencari apakah kata kunci ada di 'title' ATAU 'content'
            queryset = queryset.filter(
                Q(title__icontains=search_param) | Q(content__icontains=search_param)
            )

        return queryset


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = "slug"

    def get(self, request, *args, **kwargs):
        post = self.get_object()

        # Auto add + 1 in field 'views'
        #
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        user = request.user if request.user.is_authenticated else None
        # Batasan waktu pencegahan spam (misal: tidak dihitung jika sudah berkunjung dalam 24 jam terakhir)
        time_thresold = timezone.now() - timedelta(hours=24)

        # Cek apakah sudah ada log untuk user atau IP ini dalam 24 jam terakhir.
        if user:
            already_viewed = PostViewLog.objects.filter(
                post=post, user=user, timestamp__gte=time_thresold
            ).exists()
        else:
            already_viewed = PostViewLog.objects.filter(
                post=post, ip_address=ip, timestamp__gte=time_thresold
            ).exists()

        if not already_viewed:
            # Simpan log baru
            PostViewLog.objects.create(post=post, user=user, ip_address=ip)
            # Tambah hitungan views
            post.views += 1
            post.save()
        return super().get(request, *args, **kwargs)


class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [
        IsAdminOrReadOnly,
    ]
    pagination_class = CustomLimitOffsetPagination


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = CustomLimitOffsetPagination
    lookup_field = "slug"


"""
COMMENT
"""


class CommentListView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        post_slug = self.kwargs.get("slug")
        user = self.request.user

        # Base queryset untuk post terkait
        queryset = Comment.objects.filter(post__slug=post_slug)

        # Cek apakah post status itu DRAFTED atau PUBLISHED, jika masih DRAFTED maka tidak bisa di lihat oleh user lain
        # kecuali si author sendiri
        post = Post.objects.get(slug=post_slug)
        is_drafted = False
        is_author = False
        if post.status == Post.DRAFTED:
            is_drafted = True
        if post.author == user:
            is_author = True
        if is_drafted and is_author is False:
            raise Http404

        # Selesaikan :TODO Hanya menampilkan yang di-approve ATAU milik commenter itu sendiri
        if user.is_authenticated:
            # Cek apakah post milik user yang sedang login
            is_owner = False
            post = Post.objects.get(slug=post_slug)
            if post.author == user:
                is_owner = True
            else:
                is_owner = False

            if not is_owner:
                return queryset.filter(Q(is_approved=True) | Q(commenter=user))
            return queryset

        # Jika user anonim, mutlak hanya bisa melihat yang sudah di-approve
        return queryset.filter(is_approved=True)

    def perform_create(self, serializer):
        post_slug = self.kwargs.get("slug")
        post_obj = get_object_or_404(Post, slug=post_slug)
        serializer.save(commenter=self.request.user, post=post_obj)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [
        # permissions.IsAuthenticated,
        # # IsOwnerPostOrCommenterReadOnly,
        IsOwnerOrCommenter,
    ]
    lookup_url_kwarg = "id"

    def get_object(self):
        slug = self.kwargs.get("slug")
        comment_id = self.kwargs.get("id")
        comment_obj = get_object_or_404(Comment, id=comment_id, post__slug=slug)
        self.check_object_permissions(self.request, comment_obj)

        return comment_obj


class CommentReplyListView(generics.ListCreateAPIView):
    serializer_class = CommentReplySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomLimitOffsetPagination

    def get_queryset(self):
        slug = self.kwargs.get("slug")
        comment_id = self.kwargs.get("comment_id")
        user = self.request.user

        # Filter awal: pastikan reply milik comment_id dan slug yang cocok
        queryset = CommentReply.objects.filter(
            comment_id=comment_id, comment__post__slug=slug
        )

        # Selesaikan :TODO Hanya menampilkan yang di-approve ATAU milik commenter itu sendiri
        if user.is_authenticated:
            # Cek apakah post milik user yang sedang login
            is_owner = False
            post = Post.objects.get(slug=slug)
            if post.author == user:
                is_owner = True
            else:
                is_owner = False

            if not is_owner:
                return queryset.filter(Q(is_approved=True) | Q(commenter=user))
            return queryset
        return queryset.filter(is_approved=True)

    def perform_create(self, serializer):
        slug = self.kwargs.get("slug")
        comment_id = self.kwargs.get("comment_id")

        # Validasi memastikan komentarnya memang ada di post tersebut sebelum membalas
        comment_obj = get_object_or_404(Comment, id=comment_id, post__slug=slug)

        serializer.save(commenter=self.request.user, comment=comment_obj)


class CommentReplyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentReplySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self):
        slug = self.kwargs.get("slug")
        comment_id = self.kwargs.get("comment_id")
        reply_id = self.kwargs.get("reply_id")

        # Validasi berlapis: Reply harus milik Comment, dan Comment harus milik Post
        reply_obj = get_object_or_404(
            CommentReply, id=reply_id, comment_id=comment_id, comment__post__slug=slug
        )
        self.check_object_permissions(self.request, reply_obj)
        return reply_obj

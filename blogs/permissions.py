from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_superuser


class IsAdminOrPostOwnerReadOnly(permissions.BasePermission):
    """
    Izin khusus untuk approval komentar:
    - GET: Semua orang boleh melihat.
    - PATCH 'is_approved': Hanya Admin/Staf ATAU Pemilik POST.
    - PATCH isi (title/content): Hanya Pemilik KOMENTAR (Commenter).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # hanya owner yang boleh mengedit seluruh data post
        return obj.post.author == request.user


class IsOwnerPostOrCommenterReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # hanya admin, staff dan owner(author) yang boleh merubah field is_approved
        if "is_approved" in request.data:
            is_admin_staff = request.user and (
                request.user.is_staff or request.user.is_superuser
            )
            return is_admin_staff

        return obj.commenter == request.user


class IsOwnerOrCommenter(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        v = request.user.is_staff or (request.user == obj.post.author)
        print(v)
        return request.user.is_staff or (request.user == obj.post.author)

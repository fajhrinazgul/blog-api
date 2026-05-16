from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, password, **extra_fields):
        if not username:
            raise ValueError(_("Username is must set"))
        if not email:
            raise ValueError(_("Email is must set."))
        email = self.normalize_email(email)
        user = self.model(first_name=first_name, last_name=last_name, username=username,
                          email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, first_name, last_name, username, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(first_name, last_name, username, email, password, **extra_fields)

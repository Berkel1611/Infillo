from typing import Any

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Creates users who log in with e-mail or username."""

    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email: str | None) -> str:
        # Django lowercases only the domain; we treat the whole address case-insensitively
        return (email or "").strip().lower()

    def _create_user(self, email: str, username: str, password: str | None, **extra_fields: Any):
        if not email:
            raise ValueError("The email must be set")
        if not username:
            raise ValueError("The username must be set")
        user = self.model(
            email=self.normalize_email(email),
            username=self.model.normalize_username(username),  # Unicode normalization (NFKC)
            **extra_fields,
        )
        user.set_password(password)  # None -> unusable password (account without a password)
        user.save(using=self._db)
        return user

    def create_user(
        self, email: str, username: str, password: str | None = None, **extra_fields: Any
    ):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(
        self, email: str, username: str, password: str | None = None, **extra_fields: Any
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields["is_staff"] is not True or extra_fields["is_superuser"] is not True:
            raise ValueError("A superuser must have is_staff=True and is_superuser=True")
        return self._create_user(email, username, password, **extra_fields)

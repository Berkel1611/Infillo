from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.db.models.functions import Lower

from apps.accounts.managers import UserManager

username_validator = RegexValidator(
    # Like Django's default, but without "@": a login containing "@" is always an e-mail
    regex=r"^[\w.+-]+\Z",
    message="Enter a valid username: letters, digits and . + - _ only.",
    code="invalid_username",
)

# Role names as exposed by the API (the "role" field) and the group that marks a moderator
ROLE_USER = "user"
ROLE_MODERATOR = "moderator"
ROLE_ADMIN = "admin"
MODERATORS_GROUP = "moderators"


class User(AbstractUser):
    """Logs in with e-mail or username; username is the public name shown in the community."""

    username = models.CharField(
        "username",
        max_length=30,
        unique=True,
        validators=[MinLengthValidator(3), username_validator],
        error_messages={"unique": "A user with that username already exists."},
    )
    email = models.EmailField("email address", unique=True)
    # Redefined to make them required (AbstractUser allows blank) and set our limits
    first_name = models.CharField("first name", max_length=50)
    last_name = models.CharField("last name", max_length=80)

    USERNAME_FIELD = "email"  # used for login and by createsuperuser
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]  # extra prompts in createsuperuser

    objects = UserManager()

    class Meta:
        constraints = [
            # "Jan" and "jan" are the same username (login is case-insensitive)
            models.UniqueConstraint(Lower("username"), name="uq_user_username_lower"),
        ]

    @property
    def role(self) -> str:
        """Derived from existing data, there is no role column:
        superuser -> admin, group - > moderator."""
        if self.is_superuser:
            return ROLE_ADMIN
        # .all() reuses the cache filled by prefetch_related("groups"), so lists of users
        # need no extra query per row (a .filter(...).exists() would bypass the cache)
        if any(group.name == MODERATORS_GROUP for group in self.groups.all()):
            return ROLE_MODERATOR
        return ROLE_USER

    def __str__(self) -> str:
        return self.email

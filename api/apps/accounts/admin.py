from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from apps.accounts.models import User


class UserCreateForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")


class UserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
        field_classes = {}  # the base form maps a "username" field we no longer have


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Developer tool only — the graded admin screens live in the Next.js frontend."""

    form = UserEditForm
    add_form = UserCreateForm
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "usable_password",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

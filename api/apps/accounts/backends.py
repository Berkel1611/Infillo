from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """Login with e-mail or username. "@" cannot appear in a
    username, so it decides which."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            # The Django admin form passes the login under the USERNAME_FIELD too
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None

        login = username.strip()
        # E-mails are stored lowercase; usernames are case-insensitive
        lookup = {"email": login.lower()} if "@" in login else {"username__iexact": login}
        try:
            user = UserModel._default_manager.get(**lookup)
        except UserModel.DoesNotExist:
            # Hash anyway, so an unknown account takes
            # as long a known one (mitigates timing attacks)
            UserModel().set_password(password)
            return None

        # check_password is False for accounts without a password;
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

from django.urls import path

from apps.accounts.views import LoginView, LogoutView, MeView, MyAddressView, RegisterView

urlpatterns = [
    path("auth/register", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/me", MeView.as_view()),
    path("auth/me/address", MyAddressView.as_view()),
]

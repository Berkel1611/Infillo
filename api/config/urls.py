from django.contrib import admin
from django.urls import path

from apps.core.views import health

urlpatterns = [
    path("health", health),
    path("admin/", admin.site.urls),  # Django admin — developer tool only
]

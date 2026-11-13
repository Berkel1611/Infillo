from django.contrib import admin
from django.urls import path

from apps.core.views import health

urlpatterns = [
    path("health", health),
    path("admin/", admin.site.urls),  # Django admin — developer tool only
]

handler404 = "apps.core.views.not_found"
handler500 = "apps.core.views.server_error"

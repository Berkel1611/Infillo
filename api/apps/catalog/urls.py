from rest_framework.routers import SimpleRouter

from apps.catalog.views import CategoryViewSet, ProductViewSet

router = SimpleRouter(trailing_slash=False)
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls

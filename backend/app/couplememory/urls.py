from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CoupleMemoryViewSet, MemoryEntryViewSet, MemoryCommentViewSet, FamilyMenuViewSet

app_name = 'couplememory'

router = DefaultRouter()
router.register(r"memories", CoupleMemoryViewSet, basename="couplememory")
router.register(r"entries",  MemoryEntryViewSet,    basename="memoryentry")
router.register(r"comments", MemoryCommentViewSet,  basename="memorycomment")
router.register(r'family-menu', FamilyMenuViewSet, basename='family-menu')

urlpatterns = [
    path("", include(router.urls)),
]

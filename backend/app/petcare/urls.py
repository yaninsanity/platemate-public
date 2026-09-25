# apps/petcare/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PetViewSet,
    RewardBoxViewSet,
    MissionViewSet,
    BadgeViewSet,
    ActivityViewSet,
    ReminderViewSet,
    ReminderRuleViewSet,
    PetMessageViewSet,
    PetMessageStateViewSet,
    FoodInventoryViewSet,
)

app_name = "petcare"

router = DefaultRouter()
# -------- core endpoints ----------
router.register(r"pet",           PetViewSet,          basename="pet")
router.register(r"boxes",         RewardBoxViewSet,    basename="box")
router.register(r"missions",      MissionViewSet,      basename="mission")
router.register(r"badges",        BadgeViewSet,        basename="badge")
router.register(r"activities",    ActivityViewSet,     basename="activity")
# -------- reminders & rules ----------
router.register(r"reminders",     ReminderViewSet,     basename="reminder")
router.register(r"reminder-rules", ReminderRuleViewSet, basename="reminderrule")
# -------- pet message board ----------
router.register(r"pet-messages",  PetMessageViewSet,   basename="petmessage")
# -------- pet message state ----------
router.register(r"pet-message-state", PetMessageStateViewSet, basename="petmessagestate")
# -------- food inventory ----------
router.register(r"food-inventory", FoodInventoryViewSet, basename="foodinventory")

urlpatterns = [
    path("", include(router.urls)),
]

# cookai/urls.py
from django.urls import path
from .views import ScoreImageView, CompareImagesView, DetectIngredientsView

app_name = "cookai"

urlpatterns = [
    path("score/",  ScoreImageView.as_view(),     name="score-image"),
    path("compare/", CompareImagesView.as_view(), name="compare-images"),
    path("detect/", DetectIngredientsView.as_view(), name="detect-ingredients"),
]

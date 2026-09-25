from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet, RecipeViewSet, RecipeIngredientTaskViewSet,
    FamilyRecipeViewSet, MenuViewSet, FamilyMenuViewSet,
    RoundBracketViewSet, IngredientPhotoProofViewSet,
)
from petcare.views import DicePocketViewSet

router = DefaultRouter()
router.register(r'ingredients',      IngredientViewSet,           basename='ingredient')
router.register(r'recipes',          RecipeViewSet,               basename='recipe')
router.register(r'tasks',            RecipeIngredientTaskViewSet, basename='recipe-task')
router.register(r'family-recipes',   FamilyRecipeViewSet,         basename='family-recipe')
router.register(r'menus',            MenuViewSet,                 basename='menu')
router.register(r'family-menus',     FamilyMenuViewSet,           basename='family-menu')
router.register(r'brackets',         RoundBracketViewSet,         basename='roundly-bracket')
router.register(r'dice-pocket',      DicePocketViewSet,           basename='dice-pocket')
router.register(
    r'ingredient-photo-proofs',
    IngredientPhotoProofViewSet,
    basename='ingredient-photo-proof'
)

urlpatterns = [
    path('', include(router.urls)),
]

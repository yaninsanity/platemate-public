# ─── Monkey‐patch to ignore “redundant source” AssertionError ─────────────────────
from rest_framework.fields import Field
from urllib.parse import urlsplit, urlunsplit
_original_bind = Field.bind

def _patched_bind(self, field_name, parent):
    try:
        _original_bind(self, field_name, parent)
    except AssertionError as e:
        msg = str(e)
        if "It is redundant to specify `source`" in msg:
            # force source→field_name and carry on
            self.source = field_name
        else:
            raise

Field.bind = _patched_bind
# ────────────────────────────────────────────────────────────────────────────────

from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import serializers
from django.apps import apps
from django.db.models import Avg
from rest_framework.reverse import reverse

from rest_framework.fields import ImageField
from django.conf import settings
from .models import (
    Ingredient,
    Recipe,
    IngredientInRecipe,
    RecipeIngredientTask,
    FamilyRecipe,
    Menu,
    FamilyMenu,
    RoundBracket,
    IngredientPhotoProof
)
from django.core.files.uploadedfile import InMemoryUploadedFile

User = get_user_model()


# class AbsoluteImageField(ImageField):
#     def to_representation(self, value):
#         request = self.context.get('request')
#         if request and value:
#             return request.build_absolute_uri(value.url)
#         return super().to_representation(value)
# serializers.py 里 AbsoluteImageField
class AbsoluteImageField(ImageField):
    def to_representation(self, value):
        request = self.context.get("request")
        if not (request and value):
            # 依然保持 DRF 默认逻辑
            return super().to_representation(value)

        # 🔧 修复生产环境端口问题：使用正确的HTTPS端口
        if hasattr(settings, 'HTTPS_PORT') and settings.HTTPS_PORT:
            # 构建使用正确端口的URL
            base_url = f"https://{request.get_host().split(':')[0]}:{settings.HTTPS_PORT}"
            return f"{base_url}{value.url}"
        else:
            # 开发环境或未设置HTTPS_PORT时的回退逻辑
            raw = request.build_absolute_uri(value.url).replace(request.get_host(), f"{request.get_host()}:911")
            parts = urlsplit(raw)
            # ⬇️ 只要 host 是 docker-service 名 "web" 就返回相对路径
            if parts.hostname == "web":
                return value.url          # ==>  /media/recipes/Egg_Fried_Rice.jpg
            # 其他情况保持绝对 URL
            return raw

# ------------------------------------------------------------------
# 1. Ingredient
# ------------------------------------------------------------------
class IngredientSerializer(serializers.ModelSerializer):
    default_picture = AbsoluteImageField()

    class Meta:
        model = Ingredient
        fields = (
            "id", "name", "default_picture", "info",
            "created_at", "updated_at"
        )
        read_only_fields = ("id", "created_at", "updated_at")

# ------------------------------------------------------------------
# 2. IngredientInRecipe
# ------------------------------------------------------------------
class IngredientInRecipeSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
        write_only=True,
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            "id", "ingredient", "ingredient_id",
            "quantity", "created_at", "updated_at"
        )
        read_only_fields = ("id", "created_at", "updated_at")

# ------------------------------------------------------------------
# 3. Recipe
# ------------------------------------------------------------------
# ─── 3. Recipe ─────────────────────────────────────────────
class RecipeSerializer(serializers.ModelSerializer):
    # 👇 放在类体，DRF 才会识别为字段
    default_picture = AbsoluteImageField()

    main_ingredient = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), allow_null=True
    )
    ingredients_detail = IngredientInRecipeSerializer(
        source="ingredientinrecipe_set", many=True, read_only=True
    )
    ingredient_count = serializers.IntegerField(read_only=True)
    family_recipes   = serializers.SerializerMethodField()
    # Couple-aware AI insights for this recipe (added on retrieve)
    ai_insights      = serializers.SerializerMethodField()

    class Meta:
        model  = Recipe
        fields = (
            "id", "name", "slug",
            "preparation",               # ← preparation 已在字段里
            "instructions", "cuisine", "dish_type", "default_picture",
            "main_ingredient", "ingredient_count", "ingredients_detail",
            "family_recipes",
            "ai_insights",
            "created_at", "updated_at"
        )
        read_only_fields = (
            "id", "slug", "ingredient_count",
            "ingredients_detail", "family_recipes",
            "created_at", "updated_at"
        )

    def get_family_recipes(self, obj):
        from .serializers import FamilyRecipeSerializer
        qs = obj.family_recipes.all()
        return FamilyRecipeSerializer(qs, many=True, context=self.context).data

    def get_ai_insights(self, obj):
        """Return AI scoring summary and recent items for this recipe.
        Only computed when view context sets include_ai=True to avoid list N+1.
        Structure:
        {
          count: int,
          avg_score: float,
          recent: [ { entry_id, author, score, summary, created_at, media_url } ]
        }
        """
        if not self.context.get("include_ai"):
            return None

        request = self.context.get("request")
        user_couple = getattr(getattr(request, "user", None), "couple", None) if request else None

        MemoryEntry = apps.get_model("couplememory", "MemoryEntry")

        qs = (
            MemoryEntry.objects
            .filter(recipe=obj)
            .select_related("author")
            .prefetch_related("media")
        )
        if user_couple:
            qs = qs.filter(memory__couple=user_couple)

        judged = qs.filter(ai_judgment__isnull=False)
        count = judged.count()
        if count == 0:
            return {"count": 0, "avg_score": 0.0, "recent": []}

        avg_score = (
            judged.aggregate(avg=Avg("ai_judgment__overall_score")).get("avg") or 0.0
        )

        # recent up to 5
        recent_entries = (
            judged.select_related("ai_judgment")
                  .order_by("-ai_judgment__created_at")[:5]
        )

        recent = []
        for e in recent_entries:
            j = getattr(e, "ai_judgment", None)
            recent.append({
                "entry_id": e.id,
                "author": e.author.username,
                "score": float(j.overall_score) if j else None,
                "summary": (j.individual_summary if (j and j.individual_summary) else (j.ai_summary if j else "")),
                "created_at": (j.created_at.isoformat() if j else e.created_at.isoformat()),
                "media_url": e.best_media_url(),
            })

        return {
            "count": count,
            "avg_score": round(float(avg_score), 1),
            "recent": recent,
        }

# ------------------------------------------------------------------
# 4. RecipeIngredientTask
# ------------------------------------------------------------------
# recipes/serializers.py
class RecipeIngredientTaskSerializer(serializers.ModelSerializer):
    # ① 只读 quantity
    quantity = serializers.SerializerMethodField()

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.only("id"))
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.only("id"),
        source="ingredient",
        write_only=True,
    )

    class Meta:
        model = RecipeIngredientTask
        fields = (
            "id", "recipe", "user", "couple",
            "ingredient", "ingredient_id",
            "quantity",          # ← 新增
            "is_uploaded", "is_verified", "scanned_at",
            "created_at", "updated_at"
        )
        read_only_fields = ("id", "ingredient", "quantity", "is_uploaded", "is_verified", "scanned_at", "created_at", "updated_at")

    # ② 从 IngredientInRecipe 取份量
    def get_quantity(self, obj):
        # 使用缓存避免 N+1；_cached_quantity 为自定义属性
        if not hasattr(obj, "_cached_quantity"):
            link = IngredientInRecipe.objects.filter(
                recipe=obj.recipe_id, ingredient=obj.ingredient_id
            ).first()
            obj._cached_quantity = link.quantity if link else ""
        return obj._cached_quantity
        # 自动把当前用户的 couple 带进去（若有）
    def create(self, validated_data):
        validated_data.setdefault(
            "couple",
            getattr(self.context["request"].user, "couple", None),
        )
        return super().create(validated_data)

# ------------------------------------------------------------------
# 5. FamilyRecipe / Menu / FamilyMenu
# ------------------------------------------------------------------
class FamilyRecipeSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(), source="recipe", write_only=True
    )
    couple = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FamilyRecipe
        fields = (
            "id", "couple", "recipe", "recipe_id",
            "is_locked", "unlocked_at", "reason",
            "created_at", "updated_at"
        )
        read_only_fields = (
            "id", "couple", "recipe",
            "is_locked", "unlocked_at", "reason",
            "created_at", "updated_at"
        )

class MenuSerializer(serializers.ModelSerializer):
    recipes = serializers.PrimaryKeyRelatedField(many=True, queryset=Recipe.objects.all())

    class Meta:
        model = Menu
        fields = ("id", "name", "description", "recipes", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

class FamilyMenuSerializer(serializers.ModelSerializer):
    menu = MenuSerializer(read_only=True)
    menu_id = serializers.PrimaryKeyRelatedField(
        queryset=Menu.objects.all(), source="menu", write_only=True
    )
    couple = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FamilyMenu
        fields = (
            "id", "couple", "menu", "menu_id",
            "is_locked", "unlocked_at", "reason",
            "created_at", "updated_at"
        )
        read_only_fields = (
            "id", "couple", "menu", "is_locked", "unlocked_at",
            "reason", "created_at", "updated_at"
        )

# ------------------------------------------------------------------
# 7. RoundBracket
# ------------------------------------------------------------------
class RoundBracketSerializer(serializers.ModelSerializer):
    couple  = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe  = RecipeSerializer(source="active_recipe", read_only=True)

    # ⬇️ ① 添加一行：Checklist
    ingredient_tasks = serializers.SerializerMethodField()

    class Meta:
        model  = RoundBracket
        # ⬇️ ② 把新字段挂进 fields
        fields = (
            "id", "couple",
            "round",
            "recipe", "ingredient_tasks",
            "rerolled", "rerolled_at",
            "created_at", "updated_at"
        )
        read_only_fields = fields   # 全部只读；前端不会 PATCH

    # ⬇️ ③ 实现 getter（幂等）
    def get_ingredient_tasks(self, obj):
        qs = (
            RecipeIngredientTask.objects
            .filter(couple=obj.couple, recipe=obj.active_recipe)
            .select_related("ingredient")
        )
        return RecipeIngredientTaskSerializer(
            qs, many=True, context=self.context
        ).data


class IngredientPhotoProofSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()
    task = serializers.PrimaryKeyRelatedField(queryset=RecipeIngredientTask.objects.all())
    
    class Meta:
        model = IngredientPhotoProof
        fields = ['id', 'task', 'image', 'created_at']
        read_only_fields = ['id', 'created_at']
    def validate(self, data):
        if not isinstance(data.get("image"), InMemoryUploadedFile):
            raise serializers.ValidationError({"image": "Not a valid file."})
        return data

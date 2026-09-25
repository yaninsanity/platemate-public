# apps/users/urls.py
from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    MyCoupleView,
    CreateCoupleView,
    JoinCoupleView,
    LeaveCoupleView,
)
app_name = 'users'

urlpatterns = [
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='user-register'),
    path('auth/login/',    LoginView.as_view(),    name='user-login'),
    path('auth/logout/',   LogoutView.as_view(),   name='user-logout'),

    # Profile (UserDetailView replacement)
    path('me/',            ProfileView.as_view(),   name='user-profile'),

    # Couple operations (CoupleDetailView replacement)
    path('me/couple/',            MyCoupleView.as_view(),    name='user-couple-detail'),
    path('me/couple/create/',     CreateCoupleView.as_view(), name='user-couple-create'),
    path('me/couple/join/',       JoinCoupleView.as_view(),   name='user-couple-join'),
    path('me/couple/leave/',      LeaveCoupleView.as_view(),  name='user-couple-leave'),
]

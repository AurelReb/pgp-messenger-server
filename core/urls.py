from django.contrib.auth.decorators import login_required
from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from core.views import RegisterFilterAPIView, UserViewSet, schema_view

urlpatterns = [
    path('user/', UserViewSet.as_view(
        {
            'get': 'retrieve',
            'post': 'create',
            'put': 'update',
            'patch': 'partial_update',
        }
    )),
    path('user/token/', jwt_views.TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('user/token/refresh/',
         jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('redoc/', login_required(schema_view.with_ui('redoc',
         cache_timeout=0)), name='redoc'),
    path('swagger/', login_required(schema_view.with_ui('swagger',
         cache_timeout=0)), name='swagger'),
    path('new_ws_ticket/', RegisterFilterAPIView.as_view()),
]

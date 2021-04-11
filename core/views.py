from core.permissions import IsCreationOrIsAuthenticated
from core.models import User
from core.serializers import UserSerializer
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions, authentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    CreateModelMixin, RetrieveModelMixin, UpdateModelMixin)

schema_view = get_schema_view(
    openapi.Info(
        title='PGP-Messenger API',
        default_version='v1',
        description='PGP-Messenger API',
    ),
    public=False,
    permission_classes=(permissions.IsAdminUser,),
    authentication_classes=(authentication.SessionAuthentication,),
)


class UserViewSet(CreateModelMixin,
                  RetrieveModelMixin,
                  UpdateModelMixin,
                  GenericViewSet,
                  APIView):
    serializer_class = UserSerializer
    permission_classes = (IsCreationOrIsAuthenticated,)
    authentication_classes = (authentication.SessionAuthentication,)
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "message": "User Created Successfully. Now perform Login to get your token",
        })

    def get_object(self):
        return self.request.user

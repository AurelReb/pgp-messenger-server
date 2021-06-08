from uuid import uuid4
from django.core.cache import cache
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions, authentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin
)

from pgp_messenger_back.settings import TICKET_EXPIRE_TIME
from core.permissions import IsCreationOrIsAuthenticated
from core.models import User
from core.serializers import UserSerializer


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


class RegisterFilterAPIView(APIView):
    """
        get:
            API view for retrieving ticket uuid.
    """

    def get(self, request, *args, **kwargs):
        ticket_uuid = str(uuid4())
        # Assign the new ticket to the current user
        cache.set(ticket_uuid, request.user.id, TICKET_EXPIRE_TIME)

        return Response({'ticket_uuid': ticket_uuid})

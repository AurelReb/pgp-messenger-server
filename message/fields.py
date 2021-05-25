from django.core.exceptions import ValidationError
from rest_framework.serializers import PrimaryKeyRelatedField
from core.models import User


class RelatedUserField(PrimaryKeyRelatedField):
    def get_queryset(self):
        return User.objects.all()

    def to_internal_value(self, data):
        try:
            return User.objects.get(
                username=data
            )
        except User.DoesNotExist:
            raise ValidationError(
                f"{data} doesn't exist or doesn't accept private messages")

    def to_representation(self, obj):
        return {
            'username': obj.username,
            'pgp_public': obj.pgp_public
        }

from rest_framework import serializers
from core.models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password', 'placeholder': 'Password'}
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'password',
            'pgp_public',
            'pgp_private',
            'two_factor_auth',
        )

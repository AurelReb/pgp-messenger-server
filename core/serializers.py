from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from core.models import User


class PasswordField(serializers.CharField):
    def to_internal_value(self, data):
        # Hash the password before saving the user model
        data = make_password(data)
        return data


class UserSerializer(serializers.ModelSerializer):
    password = PasswordField(
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

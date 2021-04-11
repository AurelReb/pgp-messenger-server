from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from message.models import Message, Conversation
from message.fields import RelatedUserField
from core.models import User


class MessageSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_user(self, obj):
        return obj.user.username

    def get_created_at(self, obj):
        return obj.created_at.timestamp()

    class Meta:
        model = Message
        fields = ("id", "user", "message", "created_at")


class ConversationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "pgp_public")


class ConversationReadSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True)
    users = ConversationUserSerializer(many=True)

    class Meta:
        model = Conversation
        fields = ("id", "users", "messages")


class ConversationWriteSerializer(serializers.ModelSerializer):
    users = RelatedUserField(many=True)

    class Meta:
        model = Conversation
        fields = ("users",)

    def create(self, validated_data):
        # get user list from request data
        user_list = validated_data.get("users")
        user_list.append(self.context['request'].user)
        # get queryset from the user list
        users = (User.objects
                     .filter(username__in=validated_data.get("users"))
                     .values_list('id', flat=True))
        if users.count() < 2:
            raise ValidationError("None of the given users exist")
        # after creating conversation, add corresponding users to it
        conversation = Conversation.objects.create()
        conversation.users.add(*users)
        conversation.save()
        return conversation

from rest_framework import serializers
from message.models import Message, Conversation
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


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True)
    users = ConversationUserSerializer(many=True)

    class Meta:
        model = Conversation
        fields = ("users", "messages")

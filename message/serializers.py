from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from message.models import Message, Conversation
from message.fields import RelatedUserField
from core.models import User


class MessageSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    def get_user(self, obj):
        return obj.user.username

    def get_created_at(self, obj):
        return obj.created_at.timestamp()

    def get_updated_at(self, obj):
        return obj.updated_at.timestamp()

    class Meta:
        model = Message
        fields = (
            'id',
            'user',
            'conversation',
            'message',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('conversation',)

    def create(self, validated_data):
        # add user and conversation to validated_data (nested route)
        if not self.context.get('websocket'):
            conversation = Conversation.objects.get(
                pk=self.context["view"].kwargs["conversation_pk"])
            validated_data["conversation"] = conversation
            validated_data["user"] = self.context["request"].user
        else:
            validated_data["conversation"] = self.context["conversation"]
            validated_data["user"] = self.context["user"]

        return super().create(validated_data)


class ConversationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'pgp_public')


class ConversationReadSerializer(serializers.ModelSerializer):
    users = ConversationUserSerializer(many=True)
    last_user = serializers.SerializerMethodField()

    def get_last_user(self, obj):
        if obj.messages.count():
            last_message = obj.messages.order_by('-created_at').last()
            return last_message.user.username
        return None

    class Meta:
        model = Conversation
        fields = ('id', 'name', 'users', 'last_user')


class ConversationWriteSerializer(serializers.ModelSerializer):
    users = RelatedUserField(many=True)

    class Meta:
        model = Conversation
        fields = ('id', 'name', 'users')

    def create(self, validated_data):
        # get user list from request data
        user_list = validated_data.pop('users')
        user_list.append(self.context['request'].user)
        # get queryset from the user list
        users = (User.objects
                     .filter(username__in=user_list)
                     .values_list('id', flat=True))
        if users.count() < 2:
            raise ValidationError('None of the given users exist')
        # after creating conversation, add corresponding users to it
        conversation = Conversation.objects.create(**validated_data)
        conversation.users.add(*users)
        conversation.save()
        return conversation

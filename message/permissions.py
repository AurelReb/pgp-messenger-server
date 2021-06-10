from rest_framework.permissions import BasePermission


class ConversationPermission(BasePermission):
    def has_permission(self, request, view):
        conv_id = view.kwargs['conversation_pk']
        return request.user.conversations.filter(id=conv_id).count()

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from message.models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    search_fields = ('conversation', 'user')
    list_display = (
        'id',
        'get_conversation',
        'user',
        'created_at',
        'updated_at'
    )

    def get_conversation(self, obj):
        link = reverse("admin:message_conversation_change",
                       args=[obj.conversation.id])
        return format_html(f'<a href="{link}">{obj.conversation}</a>')
    get_conversation.admin_order_field = 'conversation'
    get_conversation.short_description = 'Conversation'

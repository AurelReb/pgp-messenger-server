from django.db import models
from typing_extensions import Required

# Create your models here.

class User (models.Model):
    pgp_public_key = models.CharField(Required=True, max_length=4096)
    two_factor_auth = models.BooleanField(Required=True)
    pgp_private_key = models.CharField(Required=False, max_length=4096)

    def __str__(self) -> str:
        return super().__str__()

class Message (models.Model):
    user = models.ForeignKey(Required=True)
    message = models.TextField(Required= True)
    created_at = models.DateField(auto_now_add=True)
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone


# Create your models here.


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(unique=True, null=False, blank=False, max_length=16)
    is_active = models.BooleanField(default=True)
    is_root = models.BooleanField(default=False)
    pgp_public = models.TextField(null=False,blank=False)
    two_factor_auth = models.BooleanField(null=True,blank=False)
    pgp_private = models.TextField(null=False, blank=True)


    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

class Message (models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=False)
    message = models.TextField(null=False,blank=True)
    created_at = models.DateField(auto_now_add=True)

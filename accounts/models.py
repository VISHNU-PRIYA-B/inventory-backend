from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class CustomUserManager(BaseUserManager):
    def create_user(self, name, email, password=None, **extra_fields):
        if not name:
            raise ValueError("Name is required")

        email = self.normalize_email(email)
        user = self.model(name=name, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, name, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(name, email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    name = models.CharField(max_length=150, unique=True)
    team_name = models.CharField(max_length=150, blank=True, default='')

    USERNAME_FIELD = 'name'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return f'{self.name} ({self.team_name})'

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)
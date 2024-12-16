from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
# Create your models here.

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin')
    )
    role = models.CharField(max_length=10 , choices = ROLE_CHOICES , default = 'user')
    

class Video(models.Model):
    movie_id = models.PositiveIntegerField(unique=True)
    qualities = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Movie Id : {self.movie_id}"
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


# Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = [
        ('artist', 'Artist'),
        ('client', 'Client'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username

# Artwork Model
CATEGORY_CHOICES = [
    ('Illustration', 'Illustration'),
    ('Painting', 'Painting'),
    ('Digital Art', 'Digital Art'),
    ('Sketch', 'Sketch'),
    ('Other', 'Other'),
]

class Artwork(models.Model):
    artist = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE,
        related_name='artworks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='artworks/')
    price = models.DecimalField(max_digits=8,decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.artist.username}"


class Activity(models.Model):
    ACTION_CHOICES = (
        ('added', 'Added'),
        ('edited', 'Edited'),
        ('deleted', 'Deleted'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    artwork_title = models.CharField(max_length=200)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.artwork_title} - {self.action}"

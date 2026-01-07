from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class User(AbstractUser):
    ROLE_CHOICES = [
        ('artist', 'Artist'),
        ('client', 'Client'),
    ]

    email = models.EmailField(unique=True) 
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    name = models.CharField(max_length=150, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_profile_complete = models.BooleanField(default=False)

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

    image = models.ImageField(upload_to='artworks/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Artwork by {self.artist.username}"


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
    



class Commission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_commissions')
    artist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artist_commissions')

    title = models.CharField(max_length=100)
    description = models.TextField()
    reference_image = models.ImageField(upload_to='commission_references/', blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    final_artwork = models.ImageField(upload_to='completed_artworks/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.client.username}"


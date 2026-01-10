from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone



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
        ('advance_paid', 'Advance Paid'),
        ('in_progress', 'In Progress'),
        ('shipped', 'Shipped'),        # ✅ NEW
        ('delivered', 'Delivered'),    # ✅ NEW
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_commissions')
    artist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artist_commissions')

    title = models.CharField(max_length=100)
    description = models.TextField()
    reference_image = models.ImageField(upload_to='commission_references/', blank=True, null=True)
    required_date = models.DateField()

    # 💰 PAYMENT
    advance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    advance_paid = models.BooleanField(default=False)

    # DATE TRACKING
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    advance_paid_at = models.DateTimeField(blank=True, null=True)
    in_progress_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)      # ✅ NEW
    delivered_at = models.DateTimeField(blank=True, null=True)    # ✅ NEW
    completed_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.client.username}"
    

    
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('commission_request', 'Commission Request'),
        ('advance_paid', 'Advance Paid'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('shipped', 'Shipped'),
    ]

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    commission = models.ForeignKey(
        Commission,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES
    )

    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.notification_type} → {self.receiver.username}"
    

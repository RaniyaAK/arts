from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


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


# ---------------- ARTWORK ----------------
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


# ---------------- ACTIVITY ----------------
class Activity(models.Model):
    ACTION_CHOICES = (
        ('added', 'Added'),
        ('edited', 'Edited'),
        ('deleted', 'Deleted'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    artwork_title = models.CharField(max_length=200)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.artwork_title} - {self.action}"


# ---------------- COMMISSION ----------------
class Commission(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('advance_paid', 'Advance Paid'),
        ('in_progress', 'In Progress'),
        ('completed', 'Work Completed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    commission_id = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        editable=False
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_commissions'
    )

    artist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='artist_commissions'
    )

    title = models.CharField(max_length=100)
    description = models.TextField()
    reference_image = models.ImageField(
        upload_to='commission_references/',
        blank=True,
        null=True
    )
    required_date = models.DateField()

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )

    advance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )

    advance_paid = models.BooleanField(default=False)

    payment_mode = models.CharField(
        max_length=10,
        choices=PAYMENT_MODE_CHOICES,
        null=True,
        blank=True
    )

    balance_paid = models.BooleanField(default=False)
    balance_paid_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    advance_paid_at = models.DateTimeField(blank=True, null=True)
    in_progress_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    rejection_reason = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.commission_id:
            self.commission_id = f"PAL-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.commission_id} - {self.title}"


# ---------------- NOTIFICATION ----------------
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

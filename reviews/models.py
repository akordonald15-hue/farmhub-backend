from django.db import models
from django.contrib.auth import get_user_model
from products.models import MenuItem
from django.conf import settings
User = get_user_model()

# -----------------------
# Status Choices
# -----------------------
STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    text = models.TextField(default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'menu_item']  # One review per user per item

    def __str__(self):
        return f"Review by {self.user} - {self.rating}/5"
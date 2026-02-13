# Accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, EmailVerification, CustomerProfile, FarmerProfile, VendorProfile, LogisticsAgentProfile

@receiver(post_save, sender=User)
def create_related_on_user(sender, instance: User, created, **kwargs):
    if created:
        # create verification row
        EmailVerification.objects.create(user=instance)

        # create role-specific profile
        role = instance.role
        if role == "customer":
            CustomerProfile.objects.create(user=instance)
        elif role == "farmer":
            FarmerProfile.objects.create(user=instance)
        elif role == "vendor":
            VendorProfile.objects.create(user=instance)
        elif role == "logistics":
            LogisticsAgentProfile.objects.create(user=instance)

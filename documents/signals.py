from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Role

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        office_role, _ = Role.objects.get_or_create(
            name="Офисный работник",
            defaults={'level': 1}
        )
        UserProfile.objects.create(user=instance, role=office_role)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save() 
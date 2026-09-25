# apps/users/models.py

import logging
import secrets
import string
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

# Initialize logger
logger = logging.getLogger(__name__)


def generate_couple_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class CustomUser(AbstractUser):
    """
    Extended user:
    - Inherits username/password/email/first_name/last_name
    - Adds profile fields
    """
    email          = models.EmailField('email address', blank=True, null=True)
    first_name     = models.CharField('first name', max_length=150, blank=True, null=True)
    last_name      = models.CharField('last name', max_length=150, blank=True, null=True)
    bio            = models.TextField(blank=True, null=True)
    birth_date     = models.DateField(blank=True, null=True)
    phone          = models.CharField(max_length=20, blank=True, null=True)
    phone_verified = models.BooleanField(default=False)
    timezone       = models.CharField(max_length=64, default="UTC")
    sms_opt_in     = models.BooleanField(default=True)
    email_opt_in   = models.BooleanField(default=True)
    address        = models.TextField(blank=True, null=True)
    role           = models.CharField(max_length=50, blank=True, null=True)


    class Meta:
        ordering = ['username']
        indexes = [models.Index(fields=['email'], name='user_email_idx')]

    def __str__(self):
        return self.get_full_name() or self.username

    def get_absolute_url(self):
        return reverse('user-detail', args=[self.pk])

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.localtime(timezone.now()).date()
        return (
            today.year - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    @property
    def couple(self):
        return self.couples.first()

    def join_couple(self, code: str):
        """Bind this user to a couple by code."""
        from .models import Couple
        couple = Couple.objects.join_by_code(self, code)
        logger.info(f"User {self.username} joined couple {code}")
        return couple

    def leave_couple(self):
        """Remove this user from their couple."""
        membership = self.couple_membership
        membership.delete()
        logger.info(f"User {self.username} left couple {membership.couple.code}")

    @property
    def couple_membership(self):
        return self.couplemembership_set.first()


class CoupleManager(models.Manager):
    """Manager for Couple with helper methods."""
    def create_couple(self, user_a: CustomUser, user_b: CustomUser):
        couple = self.create()
        couple.add_member(user_a)
        couple.add_member(user_b)
        return couple

    def join_by_code(self, user: CustomUser, code: str):
        try:
            couple = self.get(code=code)
        except self.model.DoesNotExist:
            logger.warning(f"Invalid code {code} for user {user.username}")
            raise ValidationError('Invalid couple code.')
        couple.add_member(user)
        return couple


class Couple(models.Model):
    """Model representing a couple of two users."""
    code       = models.CharField(
        max_length=8, unique=True, default=generate_couple_code,
        help_text='Invite code for partner'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Optional display name shown in UI (e.g. 'Alice & Bob')",
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='CoupleMembership',
        related_name='couples'
    )

    objects = CoupleManager()

    class Meta:
        verbose_name = 'Couple'
        verbose_name_plural = 'Couples'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['code'], name='couple_code_idx')]

    def __str__(self):
        if self.name:
            return '{} => {}'.format(self.name, self.code)
        else:
            return 'Couple({})'.format(self.code)

    def get_absolute_url(self):
        return reverse('couple-detail', args=[self.pk])

    def clean(self):
        if self.pk and self.members.count() > 2:
            logger.error(f'Couple {self.code} exceeds 2 members')
            raise ValidationError('A couple can have at most 2 members.')

    def add_member(self, user: CustomUser):
        if self.members.count() >= 2:
            logger.warning(f'Couple {self.code} full, cannot add {user.username}')
            raise ValidationError('Couple already has two members.')
        CoupleMembership.objects.create(couple=self, user=user)
        logger.info(f'User {user.username} added to couple {self.code}')

    def remove_member(self, user: CustomUser):
        membership = CoupleMembership.objects.filter(couple=self, user=user).first()
        if membership:
            membership.delete()
            logger.info(f'User {user.username} removed from couple {self.code}')

    @property
    def is_complete(self):
        return self.members.count() == 2
    
    @property
    def display_name(self):
        """UI name: custom → joined usernames → code."""
        if self.name:
            return self.name
        if self.is_complete:
            return " & ".join(u.username for u in self.members.all())
        return "Couple({})".format(self.code)

    @property
    def partner_list(self):
        return list(self.members.all())


class CoupleMembership(models.Model):
    """Through model linking users to a couple."""
    couple    = models.ForeignKey(Couple, on_delete=models.CASCADE)
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('couple', 'user')
        verbose_name = 'Couple Membership'
        verbose_name_plural = 'Couple Memberships'
        indexes = [models.Index(fields=['couple', 'user'], name='cm_idx')]

    def __str__(self):
        return '{} in {}'.format(self.user.username, self.couple.code)

import uuid

from django.db import models
from django.utils import timezone


class Search(models.Model):
    search_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    search_date = models.DateTimeField(default=timezone.now)
    from_hidden = models.TextField(blank=True, null=True)
    to_hidden = models.TextField(blank=True, null=True)
    from_short = models.TextField(blank=True, null=True)
    to_short = models.TextField(blank=True, null=True)
    to_date = models.TextField(blank=True, null=True)
    to_time = models.TextField(blank=True, null=True)
    distance = models.TextField(blank=True, null=True)
    travel_time = models.TextField(blank=True, null=True)
    session_id = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Search'
        verbose_name_plural = 'Search'


class Booking(models.Model):
    # From Search From
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session_id = models.TextField(blank=True, null=True)
    from_hidden = models.TextField(blank=True, null=True)
    to_hidden = models.TextField(blank=True, null=True)
    from_short = models.TextField(blank=True, null=True)
    to_short = models.TextField(blank=True, null=True)
    to_date = models.TextField(blank=True, null=True)
    to_time = models.TextField(blank=True, null=True)
    # Route
    distance = models.TextField(blank=True, null=True)
    travel_time = models.TextField(blank=True, null=True)
    # From Vehicle Form
    car_class = models.TextField(blank=True, null=True)
    rate = models.TextField(blank=True, null=True)
    # From Extra Form
    flight = models.TextField(blank=True, null=True)
    child_seat = models.TextField(blank=True, null=True)
    booster_seat = models.TextField(blank=True, null=True)
    flowers = models.TextField(blank=True, null=True)
    notes_extra = models.TextField(blank=True, null=True)
    # From Passengers Form
    name = models.TextField(blank=True, null=True)
    lastname = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    passengers = models.TextField(blank=True, null=True)
    luggage = models.TextField(blank=True, null=True)
    notes_details = models.TextField(blank=True, null=True)
    # From Billing Form
    billing_name = models.TextField(blank=True, null=True)
    billing_lastname = models.TextField(blank=True, null=True)
    billing_company = models.TextField(blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    terms = models.BooleanField(default=False)
    # General
    date_booking = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

from __future__ import unicode_literals
import datetime
from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError


# =======================================================================================
# LOCATION
# =======================================================================================
class Location(models.Model):
    location_name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.location_name


# =======================================================================================
# PERSON
# =======================================================================================
class Person(User):
    # http://www.djangobook.com/en/2.0/chapter14.html
    ROLE_CHOICES = (
        ('SC', 'Security Consultant'),
        ('EC', 'Delivery Manager'),
    )
    auto_increment_id = models.AutoField(primary_key=True)
    office = models.ForeignKey(Location, verbose_name="Base Office")
    role = models.CharField(max_length=2, choices=ROLE_CHOICES)

    def full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def __unicode__(self):
        return "%s %s" % (self.first_name, self.last_name)


# =======================================================================================
# DEVICE
# =======================================================================================
class Device(models.Model):
    OS_CHOICES = (
        ('ANDROID', 'Android'),
        ('IOS', 'iOS'),
        ('WIN', 'Windows Phone'),
        ('BB', 'BlackBerry'),
        ('OSX', 'OSX'),
        ('OTHER', 'Other (Specify in Notes)')
    )
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    notes = models.TextField(blank=True, null=True)
    asset_num = models.CharField(max_length=50, primary_key=True)
    serial_num = models.CharField(max_length=50)
    passcode = models.CharField(max_length=50)
    os_name = models.CharField(max_length=7, choices=OS_CHOICES)
    os_version = models.CharField(max_length=50)
    office = models.ForeignKey(Location)
    rooted = models.BooleanField()
        
    def hardware_info(self):
        return "{} {}".format(self.brand, self.model)
    hardware_info.description = 'Hardware Info'

    def software_info(self):
        return "{} {}".format(self.os_name, self.os_version)
    software_info.description = 'Software Info'

    def __unicode__(self):
        return "[%s] %s %s" % (self.asset_num, self.brand, self.model)


# =======================================================================================
# BOOKING
# =======================================================================================
class Booking(models.Model):
    auto_increment_id = models.AutoField(primary_key=True)
    date_from = models.DateField(verbose_name="Start date")
    date_to = models.DateField(verbose_name="End Date")
    notes = models.TextField(blank=True, null=True)
    returned = models.BooleanField(default=False, verbose_name='Device Returned?')

    person = models.ForeignKey(Person)
    device = models.ForeignKey(Device)

    def clean(self):
        # Check correct date range
        if not (self.date_from <= self.date_to):
            raise ValidationError('End of booking must come after its start')
        # Check device is not already booked
        bookings = Booking.objects.filter(device=self.device)
        conflicting = filter(lambda x: (self.date_from <= x.date_to) and (self.date_to >= x.date_from) and (self.auto_increment_id != x.auto_increment_id), bookings)
        if conflicting:
            raise ValidationError('Conflicting booking found on record')
        # Check returned only on the end date
        if self.returned is True:
            today = datetime.date.today()
            if today < self.date_to:
                raise ValidationError('A device cannot be marked as Returned before the end of the booking.')

    def __unicode__(self):
        return "%s: %s [%s --> %s]" % (self.person, self.device.asset_num, self.date_from, self.date_to)

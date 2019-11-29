from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
import datetime
from simple_history.models import HistoricalRecords

class TableGroup(models.Model):
    name = models.CharField(max_length=100)
    colour = models.CharField(max_length=100)
    user_id = models.IntegerField(null=True, blank=True)

class TableItem(models.Model):
    name = models.CharField(max_length=100)
    group = models.ForeignKey(TableGroup, related_name="tables", on_delete=models.CASCADE)
    people = models.IntegerField(default=0)
    user_id = models.IntegerField(null=True, blank=True)

class Booking(models.Model):
    
    time = models.TimeField(auto_now=False, auto_now_add=False)
    name = models.CharField(max_length=100)
    people = models.IntegerField()
    info = models.TextField()
    tel = models.CharField(max_length=100)
    date = models.DateField()
    initials = models.CharField(max_length=20)
    assign = models.CharField(max_length=100, default='')
    created_date = models.DateTimeField(auto_now_add=True)

    table = models.ForeignKey(TableItem, null=True, blank=True, related_name="table", on_delete=models.SET_NULL)

    arrived = models.BooleanField(default=False)
    cleared = models.BooleanField(default=False)

    objects = models.Manager()
    history = HistoricalRecords()
    user_id = models.IntegerField(null=True, blank=True)

    online = models.BooleanField(default=False)
    walk_in = models.BooleanField(default=False)
    
    def __str__(self):
        d = f'{str(self.date)[8:10]}/{str(self.date)[5:7]}/{str(self.date)[0:4]}' 
        return f'{d} - {str(self.time)[0:5]} - {self.name} ({self.people}) taken by {self.initials} at {str(self.created_date)[0:16]}'

class Staff(models.Model):
    name = models.CharField(max_length=100)
    booking = models.BooleanField()
    user_id = models.IntegerField(null=True, blank=True)
    
class Alert(models.Model):
    
    message = models.TextField()
    date = models.DateField()
    user_id = models.IntegerField(null=True, blank=True)
    objects = models.Manager()

class Settings(models.Model):
    restaurant_name = models.TextField()

    monday = models.CharField(max_length=100)
    tuesday = models.CharField(max_length=100)
    wednesday = models.CharField(max_length=100)
    thursday = models.CharField(max_length=100)
    friday = models.CharField(max_length=100)
    saturday = models.CharField(max_length=100)
    sunday = models.CharField(max_length=100)

    max_at_time = models.IntegerField(default="15")
    max_at_hour = models.IntegerField(default="50")

    email = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='usersettings')
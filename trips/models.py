from django.db import models


class Trip(models.Model):
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_used = models.FloatField(help_text="Hours already used in current 8-day cycle")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pickup_location} → {self.dropoff_location}"


class TripStop(models.Model):
    STOP_TYPES = [
        ('pickup', 'Pickup'),
        ('dropoff', 'Dropoff'),
        ('rest', 'Rest Break (30 min)'),
        ('sleep', 'Sleep / Off Duty (10 hrs)'),
        ('fuel', 'Fuel Stop'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stops')
    stop_type = models.CharField(max_length=20, choices=STOP_TYPES)
    location = models.CharField(max_length=255)
    arrival_time = models.FloatField(help_text="Hours from trip start")
    duration = models.FloatField(help_text="Duration in hours")
    miles_from_start = models.FloatField(default=0)

    def __str__(self):
        return f"{self.stop_type} at {self.location}"
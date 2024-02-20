from django.db import models
from django.db.models import UniqueConstraint


class APOD(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=255)
    explanation = models.TextField()
    url = models.CharField(max_length=255)
    media_type = models.CharField(max_length=32)
    service_version = models.CharField(max_length=8)
    twitter_media_id = models.CharField(max_length=128, null=True, blank=True)
    twitter_post_id = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return f"{self.date}-{self.title}-{self.media_type}"

    class Meta:
        constraints=[UniqueConstraint(fields=['date', 'title'], name='unique_date_title')]
